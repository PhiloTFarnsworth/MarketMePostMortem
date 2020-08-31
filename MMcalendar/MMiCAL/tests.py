import unittest
import os
from MMiCal import unfoldToCalendarList
from classes import Calendar, Event, Timezone, Property

class encodeDecodeTestCase(unittest.TestCase):
    def setUp(self):
        ## Do SetUp Here
        testfile = open('example.ics', 'r', encoding='UTF-8')
        self.testCalendarList = unfoldToCalendarList(testfile)
        testfile.close()

    ## Do Tests Here
    def test_Calendar_List(self):
        """Checks that our list contains one item, a calendar"""
        self.assertEqual(1, len(self.testCalendarList))
        self.assertIsInstance(self.testCalendarList[0], Calendar)

    def test_Calendar_Object(self):
        """Tests some basic properties of our example Calendar object"""
        self.assertEqual(1, len(self.testCalendarList[0].timezones))
        self.assertEqual(1, len(self.testCalendarList[0].events))
        self.assertEqual(4, len(self.testCalendarList[0].properties))
        self.assertEqual("PRODID", self.testCalendarList[0].properties[0].name)
        self.assertEqual("PUBLISH", self.testCalendarList[0].properties[3].value)
        for prop in self.testCalendarList[0].properties:
            self.assertEqual(0, len(prop.parameters))

    def test_Timezone_Object(self):
        """Tests the Timezone Object"""
        self.assertEqual(1, len(self.testCalendarList[0].timezones[0].properties))
        self.assertEqual(4, len(self.testCalendarList[0].timezones[0].standardProperties))
        self.assertEqual(0, len(self.testCalendarList[0].timezones[0].daylightProperties))

    def test_Event_Object(self):
        """Tests Event Object and Parameters"""
        self.assertEqual(14, len(self.testCalendarList[0].events[0].properties))
        for prop in self.testCalendarList[0].events[0].properties:
            if prop.name == "CREATED":
                self.assertEqual("20200827T035203Z", prop.value)
            if prop.value == "CONFIRMED":
                self.assertEqual("STATUS", prop.name)
        self.assertEqual(5, len(self.testCalendarList[0].events[0].properties[5].parameters))
        self.assertNotEqual(len(self.testCalendarList[0].events[0].properties[5].parameters), len(self.testCalendarList[0].events[0].properties[6].parameters))
        for param in self.testCalendarList[0].events[0].properties[5].parameters:
            if param == "PARTSTAT":
                self.assertIn(self.testCalendarList[0].events[0].properties[5].parameters["PARTSTAT"], ["DECLINED", "ACCEPTED"])