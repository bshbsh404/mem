from odoo import models, fields

class Governorate(models.Model):
    _name = 'owwsc.governorate'

    name = fields.Char(string="Governorate", required=True)
    code = fields.Char(string="Governorate Code")
    country_id = fields.Many2one('res.country', string="Country", required=True)

class Wilayat(models.Model):
    _name = 'owwsc.wilayat'

    name = fields.Char(string="Wilayat", required=True)
    code = fields.Char(string="Wilayat Code")
    governorate_id = fields.Many2one('owwsc.governorate', string="Governorate", required=True)
    country_id = fields.Many2one('res.country', string="Country", related='governorate_id.country_id', store=True)

class Building(models.Model):
    _name = 'owwsc.building'
    _description = 'Building'

    name = fields.Char(string="Building Name", required=True)
    level_ids = fields.One2many('owwsc.level', 'building_id', string="Levels")
    code = fields.Char(string="Building Code")
    image = fields.Image(string="Image")
    wilayat_id = fields.Many2one('owwsc.wilayat', string="Wilayat")
    governorate_id = fields.Many2one('owwsc.governorate', string="Governorate", related='wilayat_id.governorate_id', store=True)
    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
    )

class Level(models.Model):
    _name = 'owwsc.level'
    _description = 'Level'

    name = fields.Char(string="Level / Floor Name", required=True)
    building_id = fields.Many2one('owwsc.building', string="Building", required=True)
    section_ids = fields.One2many('owwsc.section', 'level_id', string="Sections")
    image = fields.Image(string="Image")
    code = fields.Char(string="Level Code")
    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.building_id.operating_unit_id.id if self.building_id and self.building_id.operating_unit_id else False,
    )


class Section(models.Model):
    _name = 'owwsc.section'
    _description = 'Section'

    name = fields.Char(string="Section / Division Name", required=True)
    level_id = fields.Many2one('owwsc.level', string="Level", required=True)
    department_ids = fields.One2many('owwsc.department', 'section_id', string="Departments")
    office_ids = fields.One2many('owwsc.office', 'section_id', string="Offices")
    meeting_hall_ids = fields.One2many('owwsc.meeting_hall', 'section_id', string="Meeting Halls")
    image = fields.Image(string="Image")
    code = fields.Char(string="Division Code")
    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.level_id.operating_unit_id.id if self.level_id and self.level_id.operating_unit_id else False,
    )


class Department(models.Model):
    _name = 'owwsc.department'
    _description = 'Department'

    name = fields.Char(string="Department Name", required=True)
    section_id = fields.Many2one('owwsc.section', string="Section / Division", required=True)
    image = fields.Image(string="Image")
    code = fields.Char(string="Department Code")
    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.section_id.operating_unit_id.id if self.section_id and self.section_id.operating_unit_id else False,
    )


class Office(models.Model):
    _name = 'owwsc.office'
    _description = 'Office'

    name = fields.Char(string="Office Name", required=True)
    section_id = fields.Many2one('owwsc.section', string="Section / Division", required=True)
    image = fields.Image(string="Image")
    code = fields.Char(string="Office Code")
    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.section_id.operating_unit_id.id if self.section_id and self.section_id.operating_unit_id else False,
    )


class MeetingHall(models.Model):
    _name = 'owwsc.meeting_hall'
    _description = 'Meeting Hall'

    name = fields.Char(string="Meeting Hall Name", required=True)
    section_id = fields.Many2one('owwsc.section', string="Section / Division", required=True)
    image = fields.Image(string="Image")
    code = fields.Char(string="Meeting Hall Code")
    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.section_id.operating_unit_id.id if self.section_id and self.section_id.operating_unit_id else False,
    )
