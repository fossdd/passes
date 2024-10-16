# digital_pass.py
#
# Copyright 2022-2024 Pablo Sánchez Rodríguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import locale
import re

from gi.repository import Gdk, GdkPixbuf, GLib, GObject


class DigitalPass(GObject.GObject):

    __gtype_name__ = 'DigitalPass'

    def __init__(self):
        super().__init__()
        self.__path = None

    def additional_information(self):
        raise NotImplementedError()

    def background_color(self):
        raise NotImplementedError()

    def barcodes(self):
        raise NotImplementedError()

    def creator(self):
        raise NotImplementedError()

    def description(self):
        raise NotImplementedError()

    def expiration_date(self):
        raise NotImplementedError()

    def file_extension(self):
        raise NotImplementedError()

    def format(self):
        raise NotImplementedError()

    def get_path(self):
        return self.__path

    def has_expired(self):
        expiration_date = self.expiration_date()
        return (expiration_date and Date.now() > expiration_date) \
                or self.voided()

    def icon(self):
        raise NotImplementedError()

    def is_updatable(self):
        raise NotImplementedError()

    def mime_type():
        raise NotImplementedError()

    def plotter(self, widget):
        raise NotImplementedError()

    def relevant_date():
        raise NotImplementedError()

    def set_path(self, new_path: str):
        self.__path = new_path

    def unique_identifier(self):
        raise NotImplementedError()

    def voided(self):
        raise NotImplementedError()

    @classmethod
    def supported_mime_types(cls):
        return [pass_type.mime_type() for pass_type in cls.__subclasses__()]

    @classmethod
    def supported_file_extensions(cls):
        return [pass_type.file_extension() for pass_type in cls.__subclasses__()]


class Barcode:

    def __init__(self, barcode_dictionary):
        self.__format = barcode_dictionary['format']
        if not self.__format:
            # Format is a required field
            raise Exception()

        self.__message = barcode_dictionary['message']
        if not self.__message:
            # Message is a required field
            raise Exception()

        self.__message_encoding = None
        if 'messageEncoding' in barcode_dictionary.keys():
            self.__message_encoding = barcode_dictionary['messageEncoding']

        self.__alt_text = None
        if 'altText' in barcode_dictionary.keys():
            self.__alt_text = barcode_dictionary['altText']

    def alternative_text(self):
        return self.__alt_text

    def format(self):
        return self.__format

    def message(self):
        return self.__message

    def message_encoding(self):
        return self.__message_encoding


class Color:

    def __init__(self, r, g, b, a = 255):
        self.__r = int(r)
        self.__g = int(g)
        self.__b = int(b)
        self.__a = int(a)

    def red(self):
        return self.__r

    def green(self):
        return self.__g

    def blue(self):
        return self.__b

    def as_gdk_rgba(self):
        rgba = Gdk.RGBA()
        rgba.red = self.__r / 255
        rgba.green = self.__g / 255
        rgba.blue = self.__b / 255
        rgba.alpha = self.__a / 255
        return rgba

    def as_tuple(self):
        return (self.__r, self.__g, self.__b)

    @classmethod
    def from_css(this_class, css_string):
        if css_string.startswith('rgb'):
            result = re.search(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
                               css_string)

            if not result or len(result.groups()) != 3:
                raise BadColor()

            r = result.group(1)
            g = result.group(2)
            b = result.group(3)

        elif css_string.startswith('#'):
            result = re.search(r'\#(\S{2})(\S{2})(\S{2})(\S{2})',
                               css_string)

            if not result or len(result.groups()) != 4:
                raise BadColor()

            r = int(result.group(2), 16)
            g = int(result.group(3), 16)
            b = int(result.group(4), 16)

        else:
            raise BadColor()

        return Color(r, g, b)

    def invert(self):
        self.__r = 255 - self.__r
        self.__g = 255 - self.__g
        self.__b = 255 - self.__b

    @classmethod
    def named(cls, color_name):
        if color_name == 'black':
            return Color(0, 0, 0, 255)
        elif color_name == 'white':
            return Color(255, 255, 255, 255)
        else:
            raise BadColor()


class Currency:

    SYMBOLS = {'CNY': '¥‎', 'EUR': '€', 'GBP': '£', 'INR': '₹', 'JPY': '¥',
               'KRW': '₩', 'RUB': '₽‎', 'USD': '$'}

    @classmethod
    def format(cls, amount, international_code):
        symbol_to_show = cls.get_symbol_from_code(international_code)
        output = locale.currency(amount, symbol=symbol_to_show, grouping=True)

        if symbol_to_show:
            localeconv = locale.localeconv()
            symbol_to_replace = localeconv['currency_symbol']

            if symbol_to_replace != symbol_to_show:
                output = output.replace(symbol_to_replace, symbol_to_show)

        return output

    @classmethod
    def get_symbol_from_code(cls, code):
        localeconv = locale.localeconv()
        local_currency_code = localeconv['int_curr_symbol']

        if code == local_currency_code:
            return localeconv['currency_symbol']

        if code in cls.SYMBOLS:
            return cls.SYMBOLS[code]

        return None


class Date:

    days_of_the_week = (_('Monday'), _('Tuesday'), _('Wednesday'),
                        _('Thursday'), _('Friday'), _('Saturday'), _('Sunday'))

    MAX = GLib.DateTime.new_utc(9999, 12, 31, 23, 59, 59)
    MIN = GLib.DateTime.new_utc(1, 1, 1, 0, 0, 0)

    def __init__(self, date):
        self.__date = date

    def __eq__(self, other):
        return self.compare(other) == 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __str__(self):
        return self.__date.to_local().format('%c')

    def as_relative_pretty_string(self):

        now = GLib.DateTime.new_now_utc()
        today = GLib.Date.new_dmy(now.get_day_of_month(),
                                  now.get_month(),
                                  now.get_year())

        this = GLib.Date.new_dmy(self.__date.get_day_of_month(),
                                 self.__date.get_month(),
                                 self.__date.get_year())

        difference_in_days = GLib.Date.days_between(today, this)

        if difference_in_days == 0:
            return _('Today')

        if difference_in_days == 1:
            return _('Tomorrow')

        if 0 < difference_in_days < 7:
            return Date.days_of_the_week[self.__date.get_day_of_week() - 1]

        return self.__date.to_local().format('%x')

    def compare(self, other):
        return self.__date.compare(other.__date)

    @classmethod
    def compare_dates(cls, date1, date2):
        if not date1 and not date2:
            return 0

        if date1 and not date2:
            return -1

        if not date1 and date2:
            return 1

        return date1.compare(date2)

    @classmethod
    def from_iso_string(cls, string):
        """
        Creates a Date corresponding to the given ISO 8601 formatted string
        """

        # Include hours and seconds if they have not been specified.
        # Why? DateTime.new_from_iso8601 does not accept times without them.

        matches = re.finditer(r'(T|t)([0-9]{2}\:?)+(\+|\-|Z)?', string)

        for match in matches:
            missing_info = None
            colon_count = match.group(0).count(':')

            if colon_count == 0:
                # Minutes and seconds are missing
                missing_info = ':00:00'
            elif colon_count == 1:
                # Seconds are missing
                missing_info = ':00'

            if missing_info:
                insertion_index = match.end() - 1
                string = string[:insertion_index] + missing_info + string[insertion_index:]

            # We are only interested in the first match
            break

        date = GLib.DateTime.new_from_iso8601(string)
        return Date(date)

    @classmethod
    def now(cls):
        date = GLib.DateTime.new_now_local()
        return Date(date)


class Image:

    def __init__(self, image_data):
        self.__data = image_data

    def as_pixbuf(self):
        loader = GdkPixbuf.PixbufLoader()
        loader.write(self.__data)
        loader.close()
        return loader.get_pixbuf()

    def as_texture(self):
        return Gdk.Texture.new_from_bytes(GLib.Bytes(self.__data))


class PassDataExtractor:
    """
    A PassDataExtractor contains a reference to a dictionary and a set of helper
    functions to easy the process of creating a pass.
    """

    def __init__(self, dictionary):
        self._dictionary = dictionary

    def _cast_to_boolean(self, value):
        """
        Protected method that creates a boolean from a string.
        """
        return True if value.lower().startswith('true') else False

    def get(self, key, type_constructor=None):
        """
        Return an element from the dictionary using the provided key.

        If a constructor is specified, it will be used to create the instance
        that will be returned.
        """
        try:
            value = None

            if key in self._dictionary:
                value = self._dictionary[key]
            else:
                # The key does not exist... nothing to do
                return None

            if not type_constructor and type(value) == dict:
                return PassDataExtractor(value)

            if type_constructor:
                if type(type_constructor) == bool:
                    value = self._cast_to_boolean(value)

                else:
                    value = type_constructor(value)

            return value

        except:
            return None

    def get_list(self, key, item_constructor=None, extra_arguments=None):
        """
        Return a list of elements from the dictionary using the provided key.

        If a constructor is specified, it will be used to create each of the
        items that will be appended to the list.
        """

        data_list = self.get(key)

        if not data_list:
            return []

        if not extra_arguments:
            extra_arguments = ()

        elif type(extra_arguments) != tuple:
            extra_arguments = (extra_arguments,)

        result = list()
        for item_data in data_list:

            if item_constructor:
                try:
                    arguments = (item_data,) + extra_arguments
                    instance = item_constructor(*arguments)
                except:
                    continue
            else:
                instance = item_data

            result.append(instance)

        return result

    def keys(self):
        """
        Return the set of keys
        """
        return self._dictionary.keys()


class PassField:

    __slots__ = ('_label',
                 '_value')

    def __init__(self):
        self._label = None
        self._value = None

    def label(self):
        return self._label

    def value(self):
        return self._value


class TimeInterval:
    def __init__(self, start_time, end_time):
        self.__start_time = start_time
        self.__end_time = end_time

    def __contains__(self, time):
        if (self.__start_time and time < self.__start_time) or \
           (self.__end_time and time > self.__end_time):
            return False

        return True

    @classmethod
    def from_iso_strings(cls, start_time, end_time):
        start_time = Date.from_iso_string(start_time) if start_time else Date.MIN
        end_time = Date.from_iso_string(end_time) if end_time else Date.MAX
        return TimeInterval(start_time, end_time)

    def end_time(self):
        return self.__end_time


class BadColor(Exception):
    pass
