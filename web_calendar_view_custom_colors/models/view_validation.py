# @ 2019 Savoir-failre Linux
# License LGPL-3.0 or Later (http://www.gnu.org/licenses/lgpl).

import collections
import logging
import os

from lxml import etree
from odoo import tools
from odoo.tools import view_validation

_logger = logging.getLogger(__name__)


_validators = collections.defaultdict(list)
_relaxng_cache = {}

original_relaxng = view_validation.relaxng


def relaxng(view_type):
    # Override the relaxng to modify calendar_view.rng calendar element
    # and modify calendar element by adding js_class attribute
    override = 'web_calendar_view_custom_colors/xsl/add_js_class_attribute.xsl'
    if view_type not in _relaxng_cache:
        rng_path = os.path.join('base', 'rng', '%s_view.rng' % view_type)
        with tools.file_open(rng_path) as frng:
            try:
                relaxng_doc = etree.parse(frng)
                # local modification
                if view_type == 'calendar':
                    transform = etree.XSLT(
                      etree.parse(tools.file_open(override)))
                    relaxng_doc = transform(relaxng_doc)
                # end local modification
                _relaxng_cache[view_type] = etree.RelaxNG(relaxng_doc)
            except Exception:
                _logger.exception(
                    'Failed to load RelaxNG XML schema for views validation')
                _relaxng_cache[view_type] = None
    return _relaxng_cache[view_type]


view_validation.relaxng = relaxng
