import unittest
from prometheus.domain.richtext import html_fragment, format_equation_html


class RichTextTests(unittest.TestCase):
    def test_body_and_style(self):
        self.assertEqual(html_fragment('<html><body><p style="color:red;font-weight:bold">Hi</p></body></html>'), '<p style="font-weight:bold">Hi</p>')

    def test_plain_text(self):
        self.assertEqual(html_fragment('A & B\nC'), 'A &amp; B<br>C')

    def test_equations(self):
        result = format_equation_html('x^{2} + H2O -> y_1', 'Química')
        for part in ('<sup>2</sup>', 'H<sub>2</sub>O', '→', 'y<sub>1</sub>'):
            self.assertIn(part, result)
