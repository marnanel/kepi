# test_activity.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.test import TestCase
from kepi.bowler_pub.models import AcObject, AcActivity
from kepi.bowler_pub.create import create
from unittest import skip
from . import remote_object_is_recorded, create_local_person
import logging

logger = logging.Logger(name='kepi')

REMOTE_ID_1 = 'https://users.example.com/activity/1'
REMOTE_ID_2 = 'https://users.example.com/item/2'

REMOTE_FRED = 'https://users.example.com/user/fred'
LOCAL_ALICE = 'https://testserver/users/alice'

SAMPLE_NOTE = {
        "id": REMOTE_ID_2,
        "type": "Note",
        }

class TestAcObject(TestCase):

    def test_bad_type(self):

        create(
            f_id = REMOTE_ID_1,
            f_type = "Wombat",
            is_local_user = False,
            )

        self.assertFalse(remote_object_is_recorded(REMOTE_ID_1),
                "objects of type Wombat don't get created")

    def test_remote_no_id(self):

        from kepi.bowler_pub.models import AcObject

        create(
            f_type = "Create",
            f_actor = REMOTE_FRED,
            f_object = SAMPLE_NOTE,
            is_local_user = False,
            sender="https://remote.example.com")

        with self.assertRaises(AcObject.DoesNotExist,
                msg="remote objects with no ID don't get created",
                ):
            result = AcActivity.objects.get(
                    f_actor=REMOTE_FRED,
                    )
            logger.warn('  -- remote object was found: %s',
                    result)

    @skip("Param errors aren't currently enforced")
    def test_create_create_wrong_params(self):

        with self.assertRaisesMessage(ValueError, "Wrong parameters for thing type"):
            create(
                f_id = REMOTE_ID_1,
                f_type = "Create",
                is_local_user = False,
                )

        with self.assertRaisesMessage(ValueError, "Wrong parameters for thing type"):
            create(
                f_id = REMOTE_ID_1,
                f_actor = REMOTE_FRED,
                f_type = "Create",
                is_local_user = False,
                )

        with self.assertRaisesMessage(ValueError, "Wrong parameters for thing type"):
            create(
                f_id = REMOTE_ID_1,
                f_target = REMOTE_FRED,
                f_type = "Create",
                is_local_user = False,
                )

    def test_create_create(self):

        create_local_person(name='alice')

        create(
            f_id = REMOTE_ID_1,
            f_type = "Create",
            f_to = LOCAL_ALICE,
            f_actor = REMOTE_FRED,
            f_object = SAMPLE_NOTE,
            is_local_user = False,
            )

        self.assertTrue(remote_object_is_recorded(REMOTE_ID_1),
                "objects of type Create get created")

        self.assertTrue(remote_object_is_recorded(REMOTE_ID_2),
                "objects of type Create create stuff")
