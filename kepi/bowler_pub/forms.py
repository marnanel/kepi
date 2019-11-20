# forms.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This module contains some forms which are used by
the admin interface. It's not very elaborate yet.
"""

from django import forms
import kepi.bowler_pub.models as bowler_pub_models

class NoteAdminForm(forms.ModelForm):

    class Meta:
        model = bowler_pub_models.AcNote

        fields = [
                'f_content',
                'f_attributedTo',
            ]

    f_content = forms.CharField(
            widget = forms.Textarea)
