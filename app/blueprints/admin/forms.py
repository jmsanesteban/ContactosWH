from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Optional


class UserForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(3, 64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 128)])
    role = SelectField('Rol', choices=[('user', 'Usuario'), ('admin', 'Administrador')])
    is_active = BooleanField('Cuenta activa', default=True)
    submit = SubmitField('Guardar')


class ImportForm(FlaskForm):
    file = FileField('Archivo Excel', validators=[
        FileRequired(),
        FileAllowed(['xlsx', 'xls'], 'Solo se permiten archivos Excel (.xlsx, .xls)')
    ])
    update_existing = BooleanField('Actualizar contactos existentes (por nombre y apellidos)')
    submit = SubmitField('Importar')


class FieldForm(FlaskForm):
    display_name = StringField('Nombre visible', validators=[DataRequired(), Length(1, 128)])
    submit = SubmitField('Guardar')


class ExportForm(FlaskForm):
    contact_ids = HiddenField()
    visible_fields_only = BooleanField('Solo campos visibles', default=True)
    submit = SubmitField('Exportar a Excel')
