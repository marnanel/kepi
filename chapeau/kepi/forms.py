# forms.py
#
# Part of chapeau, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This module contains some forms which are used by
the admin interface. It's not very elaborate yet.
"""

from django import forms
import chapeau.kepi.models as kepi_models

class NoteAdminForm(forms.ModelForm):

    class Meta:
        model = kepi_models.AcNote

        fields = [
                'f_content',
                'f_attributedTo',
            ]

    f_content = forms.CharField(
            widget = forms.Textarea)
