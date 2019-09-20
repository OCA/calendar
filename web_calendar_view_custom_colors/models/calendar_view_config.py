# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class CalendarViewConfig(models.Model):
    _name = 'calendar.view.config'

    name = fields.Char(
        string='Description',
        required=True,
    )
    model_id = fields.Many2one(
        string='Calendar Model',
        comodel_name='ir.model',
        required=True,
        help="The model to which the tag rule applies."
    )
    model_name = fields.Char(
        related='model_id.model',
        readonly=True,
    )
    allow_calendar_tag_color = fields.Boolean(
        string='Display calendar with tag colors',
        default=False,
    )
    tag_field_id = fields.Many2one(
        string='Tag Field',
        comodel_name='ir.model.fields',
    )
    color_field_id = fields.Many2one(
        string='Color Tag Field',
        comodel_name='ir.model.fields',
    )
    font_color_field_id = fields.Many2one(
        string='Font Color Tag Field',
        comodel_name='ir.model.fields',
    )
    allow_calendar_hatched = fields.Boolean(
        string='Display calendar with hatched states',
        default=False,
    )
    calendar_state_field_id = fields.Many2one(
        string='Calendar State Field',
        comodel_name='ir.model.fields',
    )
    hatched_states = fields.Char(
        string='Calendar Hatched States',
        help='Put the different states that should appear on hatched style '
             'separated by -. Example: draft-cancel'
    )

    _sql_constraints = [
        ('calendar_model_uniq', 'unique (model_id)', "Calendar Model already"
                                                     " exist!"),
    ]

    @api.onchange('model_id')
    def onchange_model_id(self):
        if self.model_id:
            res = {
                'domain': {
                    'tag_field_id': [('model_id', '=', self.model_id.id),
                                     ('ttype', '=', 'many2one')],
                    'calendar_state_field_id': [
                        ('model_id', '=', self.model_id.id),
                        ('ttype', 'in', ['selection', 'many2one'])],
                }
            }
            return res

    @api.onchange('tag_field_id')
    def onchange_tag_field_id(self):
        if self.tag_field_id:
            relation = self.tag_field_id.relation
            res = {
                'domain': {
                    'color_field_id': [('model', '=', relation),
                                       ('ttype', '=', 'char')
                                       ],
                    'font_color_field_id': [
                        ('model', '=', relation),
                        ('ttype', '=', 'selection')]}
            }
            return res

    @api.onchange('calendar_state_field_id')
    def onchange_calendar_state_field_id(self):
        if self.calendar_state_field_id:
            res = {
                'help': {
                        'hatched_states': 'hello',
                }
            }
            return res

    @staticmethod
    def get_field_name(field_id):
        name = ''
        if field_id:
            return field_id.name
        return name

    @staticmethod
    def get_field_relation(field_id):
        relation = ''
        if field_id:
            return field_id.relation
        return relation

    @api.model
    def get_calendar_tag_values(self, model_name):
        def Convert(string):
            li = list(string.split("-"))
            return li
        res = []
        calendar_config = self.env['calendar.view.config'].search(
            [('model_name', '=', model_name)], limit=1)
        if not calendar_config[
            'allow_calendar_tag_color'
        ] and not calendar_config['allow_calendar_hatched']:
            return res
        hatched = False
        color = False
        font_color = False
        calendar_obj = self.env[model_name]
        calendars = calendar_obj.search([])

        if calendar_config:
            for calendar in calendars:
                if calendar_config['allow_calendar_hatched'] and\
                        calendar_config['hatched_states']:
                    calendar_state_field_name = self.get_field_name(
                        calendar_config['calendar_state_field_id'])
                    hatched = calendar[calendar_state_field_name] in Convert(
                        calendar_config['hatched_states'])
                if calendar_config['allow_calendar_tag_color']:
                    tag_field_name = self.get_field_name(
                        calendar_config['tag_field_id'])
                    tag = calendar[tag_field_name]
                    color_field_name = self.get_field_name(
                        calendar_config['color_field_id'])
                    font_color_field_name = self.get_field_name(
                        calendar_config['font_color_field_id'])
                    color = tag[color_field_name]
                    font_color = tag[font_color_field_name]
                res.append(
                    {
                        'id': calendar.id,
                        'color': color,
                        'font_color': font_color,
                        'hatched': hatched,
                    }
                )
        return res
