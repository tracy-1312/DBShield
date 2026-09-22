import unittest

from backend.password_policy import password_checks, password_validation_errors


class PasswordPolicyTests(unittest.TestCase):
    def test_accepts_a_strong_password(self):
        self.assertEqual(
            password_validation_errors(
                "River!Quartz7Maple",
                username="jsmith",
                email="jsmith@hospital.com",
            ),
            [],
        )

    def test_reports_each_missing_character_group(self):
        errors = password_validation_errors("alllowercase")

        self.assertIn("include an uppercase letter", errors)
        self.assertIn("include a number", errors)
        self.assertIn("include a symbol", errors)

    def test_rejects_short_and_common_passwords(self):
        checks = password_checks("password123")

        self.assertFalse(checks["minimum_length"])
        self.assertFalse(checks["uppercase"])
        self.assertFalse(checks["symbol"])
        self.assertFalse(checks["not_common"])

    def test_rejects_username_and_email_name(self):
        username_errors = password_validation_errors(
            "JSmiTh!Secure2026",
            username="jsmith",
        )
        email_errors = password_validation_errors(
            "Doctor.Brown!2026",
            email="doctor.brown@hospital.com",
        )

        self.assertIn("not contain the username or email name", username_errors)
        self.assertIn("not contain the username or email name", email_errors)

    def test_enforces_bcrypt_byte_limit(self):
        errors = password_validation_errors("A1!" + "é" * 35)

        self.assertIn("use no more than 72 UTF-8 bytes", errors)


if __name__ == "__main__":
    unittest.main()
