import os
from flask import (render_template, redirect, url_for, flash, request,
                   send_file, current_app, abort, jsonify)
from flask_login import login_required, current_user
from functools import wraps
from . import admin_bp
from .forms import UserForm, ImportForm, FieldForm, ExportForm
from ...models.user import User
from ...models.contact import Contact, ContactValue
from ...models.field import FieldDefinition
from ...extensions import db
from ...utils.security import generate_secure_password
from ...utils.excel import parse_excel, export_to_excel


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_contacts': Contact.query.count(),
        'visible_contacts': Contact.query.filter_by(is_visible=True).count(),
        'total_fields': FieldDefinition.query.count(),
        'visible_fields': FieldDefinition.query.filter_by(is_visible=True).count(),
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
    }
    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    fields = FieldDefinition.query.filter_by(is_visible=True).order_by(FieldDefinition.field_order).limit(3).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_contacts=recent_contacts, fields=fields)


# ── Users ──────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Nuevo usuario')

        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está en uso.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Nuevo usuario')

        password = generate_secure_password()
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_active=form.is_active.data,
            must_change_password=True,
            created_by_id=current_user.id,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario creado. Contraseña temporal: <strong>{password}</strong>', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, title='Nuevo usuario')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing and existing.id != user_id:
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Editar usuario', user=user)

        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != user_id:
            flash('El email ya está en uso.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Editar usuario', user=user)

        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        db.session.commit()
        flash('Usuario actualizado correctamente.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, title='Editar usuario', user=user)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def user_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    password = generate_secure_password()
    user.set_password(password)
    user.must_change_password = True
    db.session.commit()
    flash(f'Contraseña de <strong>{user.username}</strong> restablecida: <strong>{password}</strong>', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'warning')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    state = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {state} correctamente.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'warning')
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin.users'))


# ── Fields ─────────────────────────────────────────────────────────────────

@admin_bp.route('/fields')
@login_required
@admin_required
def fields():
    all_fields = FieldDefinition.query.order_by(FieldDefinition.field_order).all()
    return render_template('admin/fields.html', fields=all_fields)


@admin_bp.route('/fields/<int:field_id>/toggle', methods=['POST'])
@login_required
@admin_required
def field_toggle(field_id):
    field = FieldDefinition.query.get_or_404(field_id)
    field.is_visible = not field.is_visible
    db.session.commit()
    return jsonify({'visible': field.is_visible})


@admin_bp.route('/fields/<int:field_id>/rename', methods=['POST'])
@login_required
@admin_required
def field_rename(field_id):
    field = FieldDefinition.query.get_or_404(field_id)
    new_name = request.form.get('display_name', '').strip()
    if not new_name:
        flash('El nombre no puede estar vacío.', 'danger')
        return redirect(url_for('admin.fields'))
    field.display_name = new_name
    db.session.commit()
    flash('Campo actualizado.', 'success')
    return redirect(url_for('admin.fields'))


@admin_bp.route('/fields/reorder', methods=['POST'])
@login_required
@admin_required
def fields_reorder():
    order = request.json.get('order', [])
    for idx, field_id in enumerate(order):
        field = FieldDefinition.query.get(field_id)
        if field:
            field.field_order = idx
    db.session.commit()
    return jsonify({'ok': True})


# ── Contacts admin ─────────────────────────────────────────────────────────

@admin_bp.route('/contacts')
@login_required
@admin_required
def contacts():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    per_page = 25

    fields = FieldDefinition.query.order_by(FieldDefinition.field_order).all()
    query = Contact.query.order_by(Contact.id.desc())

    if search:
        matching_ids = (
            ContactValue.query
            .filter(ContactValue.value.ilike(f'%{search}%'))
            .with_entities(ContactValue.contact_id)
            .distinct()
        )
        query = query.filter(Contact.id.in_(matching_ids))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/contacts.html',
                           contacts=pagination.items,
                           fields=fields,
                           pagination=pagination,
                           search=search)


@admin_bp.route('/contacts/<int:contact_id>/toggle', methods=['POST'])
@login_required
@admin_required
def contact_toggle(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.is_visible = not contact.is_visible
    db.session.commit()
    return jsonify({'visible': contact.is_visible})


@admin_bp.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
@admin_required
def contact_delete(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contacto eliminado.', 'success')
    return redirect(url_for('admin.contacts'))


@admin_bp.route('/contacts/delete-selected', methods=['POST'])
@login_required
@admin_required
def contacts_delete_selected():
    ids = request.form.getlist('contact_ids')
    if ids:
        Contact.query.filter(Contact.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'{len(ids)} contacto(s) eliminado(s).', 'success')
    return redirect(url_for('admin.contacts'))


# ── Import ─────────────────────────────────────────────────────────────────

@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_contacts():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        try:
            headers, rows = parse_excel(file.stream)
        except Exception as e:
            flash(f'Error al leer el archivo: {str(e)}', 'danger')
            return render_template('admin/import.html', form=form)

        # Normalise headers
        normalised = [h.strip().lower().replace(' ', '_') for h in headers]

        # Ensure FieldDefinitions exist
        field_map = {}
        max_order = db.session.query(db.func.max(FieldDefinition.field_order)).scalar() or 0
        for idx, (raw, norm) in enumerate(zip(headers, normalised)):
            fd = FieldDefinition.query.filter_by(name=norm).first()
            if not fd:
                fd = FieldDefinition(name=norm, display_name=raw.strip(),
                                     is_visible=True, field_order=max_order + idx + 1)
                db.session.add(fd)
                db.session.flush()
            field_map[norm] = fd

        created = updated = skipped = 0

        for row in rows:
            # Build lookup key
            key_parts = []
            for key_field in ('nombre', 'apellidos', 'name', 'apellido'):
                val = row.get(headers[normalised.index(key_field)]) if key_field in normalised else None
                if val:
                    key_parts.append(str(val).strip().lower())

            existing = None
            if form.update_existing.data and key_parts:
                # Find contacts that match on key fields
                for fd_name, key_val in zip(['nombre', 'apellidos'], key_parts):
                    if fd_name in field_map:
                        fd = field_map[fd_name]
                        cv = ContactValue.query.filter_by(field_id=fd.id, value=key_val).first()
                        if cv:
                            existing = cv.contact
                            break

            if existing:
                contact = existing
                updated += 1
            else:
                contact = Contact(is_visible=True, created_by_id=current_user.id)
                db.session.add(contact)
                db.session.flush()
                created += 1

            for raw_header, norm_name in zip(headers, normalised):
                value = row.get(raw_header)
                if value is None:
                    value = ''
                else:
                    value = str(value).strip()

                fd = field_map.get(norm_name)
                if not fd:
                    continue

                cv = ContactValue.query.filter_by(contact_id=contact.id, field_id=fd.id).first()
                if cv:
                    cv.value = value
                else:
                    db.session.add(ContactValue(contact_id=contact.id, field_id=fd.id, value=value))

        db.session.commit()
        flash(f'Importación completada: {created} creados, {updated} actualizados.', 'success')
        return redirect(url_for('admin.contacts'))

    return render_template('admin/import.html', form=form)


# ── Export ─────────────────────────────────────────────────────────────────

@admin_bp.route('/export', methods=['GET', 'POST'])
@login_required
@admin_required
def export_contacts():
    form = ExportForm()
    fields = FieldDefinition.query.order_by(FieldDefinition.field_order).all()
    contacts_list = Contact.query.order_by(Contact.id).all()

    if form.validate_on_submit():
        ids_raw = form.contact_ids.data
        if ids_raw:
            ids = [int(x) for x in ids_raw.split(',') if x.strip().isdigit()]
            selected = Contact.query.filter(Contact.id.in_(ids)).all()
        else:
            selected = contacts_list

        if form.visible_fields_only.data:
            export_fields = [f for f in fields if f.is_visible]
        else:
            export_fields = fields

        buffer = export_to_excel(selected, export_fields)
        return send_file(
            buffer,
            as_attachment=True,
            download_name='contactos_export.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return render_template('admin/export.html', form=form, fields=fields, contacts=contacts_list)
