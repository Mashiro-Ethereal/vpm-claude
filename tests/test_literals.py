import unittest

from vpmkit.artifact.literals import LiteralSyntaxError, parse_literal


class LiteralTests(unittest.TestCase):
    def test_whitespace_and_arguments(self):
        lit = parse_literal(" \tnear ( g , block_2 ) \n")
        self.assertEqual((lit.pred, lit.args, lit.positive), ("near", ("g", "block_2"), True))
        self.assertEqual(lit.instance_key, "near(g, block_2)")
        self.assertEqual(parse_literal("ready( )").args, ())

    def test_negation(self):
        for text in ["not near(g, block)", "not\tnear(g,block)", "¬near(g,block)", " ¬ near(g, block) "]:
            with self.subTest(text=text):
                lit = parse_literal(text)
                self.assertFalse(lit.positive)
                self.assertEqual(lit.instance_key, "near(g, block)")
        self.assertTrue(parse_literal("nothing(g)").positive)

    def test_syntax_errors_include_input(self):
        for text in ["", "notnear g", "near(g,)", "near(,g)", "near(g) junk",
                     "notnot near(g)", "near(1)", "x.y(g)", "near('g')", "not(g) and x()"]:
            with self.subTest(text=text), self.assertRaises(LiteralSyntaxError) as ctx:
                parse_literal(text)
            self.assertIn(repr(text), str(ctx.exception))
