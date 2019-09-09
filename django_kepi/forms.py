# forms.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This module contains some forms which are used by
the admin interface. It's not very elaborate yet.
"""

from django import forms
import django_kepi.models as kepi_models

class PersonAdminForm(forms.ModelForm):

    class Meta:
        model = kepi_models.AcPerson

        fields = [
                'f_preferredUsername',
                'f_summary',
                'icon',
                'header',
                'auto_follow',
            ]


class NoteAdminForm(forms.ModelForm):

    class Meta:
        model = kepi_models.AcNote

        fields = [
                'f_content',
                'f_attributedTo',
            ]

    f_content = forms.CharField(
            widget = forms.Textarea)
