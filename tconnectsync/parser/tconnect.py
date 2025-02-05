import sys
import arrow

try:
    from ..secret import TIMEZONE_NAME
except Exception:
    print('Unable to import parser secrets from secret.py')
    sys.exit(1)

"""
Conversion methods for parsing raw t:connect data into
a more digestable format, which is used internally.
"""
class TConnectEntry:
    BASAL_EVENTS = { 0: "Suspension", 1: "Profile", 2: "TempRate", 3: "Algorithm" }
    ACTIVITY_EVENTS = { 1: "Sleep", 2: "Exercise", 3: "AutoBolus", 4: "CarbOnly" }

    @staticmethod
    def _epoch_parse(x):
        # data["x"] is an integer epoch timestamp which, when read as an equivalent timestamp
        # stored in Pacific time (America/Los_Angeles), contains the user's local time, but
        # with the wrong timezone data attached.
        #
        # For example, data["x"] references UTC timestamp 2020-09-01T13:00:00+00:00,
        # which when read in Pacific time is equivalent to 2020-09-01T06:00:00-07:00.
        # However, the user's timezone is Eastern time, so the timezone of America/Los_Angeles
        # is overwritten with America/New_York, resulting in 2020-09-01T06:00:00-04:00, the
        # correct timestamp.
        return arrow.get(x, tzinfo="America/Los_Angeles").replace(tzinfo=TIMEZONE_NAME)

    @staticmethod
    def parse_ciq_basal_entry(data, delivery_type=""):
        time = TConnectEntry._epoch_parse(data["x"])
        duration_mins = data["duration"] / 60
        basal_rate = data["y"]

        return {
            "time": time.format(),
            "delivery_type": delivery_type,
            "duration_mins": duration_mins,
            "basal_rate": basal_rate,
        }

    @staticmethod
    def parse_suspension_entry(data):
        time = TConnectEntry._epoch_parse(data["x"])
        return {
            "time": time.format(),
            "continuation": data["continuation"],
            "suspendReason": data["suspendReason"],
        }

    @staticmethod
    def _datetime_parse(date):
        return arrow.get(date, tzinfo=TIMEZONE_NAME)

    @staticmethod
    def parse_cgm_entry(data):
        # EventDateTime is stored in the user's timezone.
        return {
            "time": TConnectEntry._datetime_parse(data["EventDateTime"]).format(),
            "reading": data["Readings (CGM / BGM)"],
            "reading_type": data["Description"],
        }

    @staticmethod
    def parse_iob_entry(data):
        # EventDateTime is stored in the user's timezone.
        return {
            "time": TConnectEntry._datetime_parse(data["EventDateTime"]).format(),
            "iob": data["IOB"],
            "event_id": data["EventID"],
        }

    @staticmethod
    def parse_csv_basal_entry(data, duration_mins=None):
        # EventDateTime is stored in the user's timezone.
        return {
            "time": TConnectEntry._datetime_parse(data["EventDateTime"]).format(),
            "delivery_type": "Unknown",
            "duration_mins": duration_mins,
            "basal_rate": data["BasalRate"],
        }

    @staticmethod
    def parse_bolus_entry(data):
        # All DateTime's are stored in the user's timezone.
        complete = (data["ExtendedBolusIsComplete"] or data["BolusIsComplete"])
        extended_bolus = ("extended" in data["Description"].lower())

        return {
            "description": data["Description"],
            "complete": "1" if complete else "",
            "completion": data["CompletionStatusDesc"] if not extended_bolus else data["BolexCompletionStatusDesc"],
            "request_time": TConnectEntry._datetime_parse(data["RequestDateTime"]).format() if complete and not extended_bolus else None,
            "completion_time": TConnectEntry._datetime_parse(data["CompletionDateTime"]).format() if complete and not extended_bolus else None,
            "insulin": data["InsulinDelivered"],
            "carbs": data["CarbSize"],
            "user_override": data["UserOverride"],
            "extended_bolus": "1" if extended_bolus else "",
            "bolex_completion_time": TConnectEntry._datetime_parse(data["BolexCompletionDateTime"]).format() if complete and extended_bolus else None,
            "bolex_start_time": TConnectEntry._datetime_parse(data["BolexStartDateTime"]).format() if complete and extended_bolus else None,
        }