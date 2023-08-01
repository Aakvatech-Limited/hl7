# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class LabMachineMessage(Document):
    def validate(self):
        self.set_missing_fields()
        self.update_lab_test()

    def after_insert(self):
        self.update_lab_test()

    def set_missing_fields(self):
        if not self.message:
            return
        msg_lines = self.message.splitlines()
        self.machine_make = msg_lines[0].split("|")[2]
        self.machine_model = msg_lines[0].split("|")[3]
        self.lab_test_name = msg_lines[3].split("|")[3]
        self.sample_collection = self.get_sample_collection(msg_lines)

    def get_sample_collection(self, msg_lines):
        for line in msg_lines:
            if line.startswith("OBR"):
                fields = line.split("|")
                if fields[2]:
                    return fields[2]
                elif fields[3]:
                    return fields[3]

    def update_lab_test(self):
        if not self.message:
            return
        if self.machine_model and self.machine_make and self.lab_test_name:
            profile_name = self.machine_model + "-" + self.machine_make
            profile_exists = frappe.db.exists("Lab Machine Profile", profile_name)
            if not profile_exists:
                return
            profile = frappe.get_doc("Lab Machine Profile", profile_name)

            lab_test_name = profile.lab_test_prefix + self.lab_test_name
            lab_test_exists = frappe.db.exists("Lab Test", lab_test_name)
            if not lab_test_exists:
                return

            lab_test = frappe.get_doc("Lab Test", lab_test_name)
            if lab_test.docstatus != 0:
                return

            msg_lines = self.message.splitlines()
            for line in msg_lines[profile.obx_nm_start : profile.obx_nm_end]:
                test_name = line.split("|")[3].split("^")[1].replace("*", "")
                test_result = line.split("|")[5]
                lab_test_row = ""
                for row in lab_test.normal_test_items:
                    if row.lab_test_name == test_name:
                        lab_test_row = row
                        break
                if lab_test_row:
                    lab_test_row.result_value = test_result

            self.lab_test = lab_test_name
            lab_test.save(ignore_permissions=True)
            frappe.db.commit()

        if self.sample_collection:
            sample_collection_doc = frappe.get_cached_doc(
                "Sample Collection", self.sample_collection
            )
            ## try to upodate each lab test in the sample collection
            for lab_test in sample_collection_doc.lab_tests:
                lab_test_doc = frappe.get_cached_doc("Lab Test", lab_test.lab_test)
                if lab_test_doc.docstatus != 0:
                    continue
                msg_lines = self.message.splitlines()
                for line in msg_lines:
                    if line.startswith("OBX"):
                        fields = line.split("|")
                        if fields[2] == "NM":
                            test_name = fields[3].split("^")[1].replace("*", "")
                            test_result = fields[5]
                            lab_test_row = ""
                            for row in lab_test_doc.normal_test_items:
                                if row.lab_test_name == test_name:
                                    lab_test_row = row
                                    break
                            if lab_test_row:
                                lab_test_row.result_value = test_result
                lab_test_doc.save(ignore_permissions=True)
                frappe.db.commit()
