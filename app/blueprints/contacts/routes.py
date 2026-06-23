from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from . import contacts_bp
from ...models.contact import Contact
from ...models.field import FieldDefinition


@contacts_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    per_page = 25

    if current_user.is_admin:
        fields = FieldDefinition.query.order_by(FieldDefinition.field_order).all()
        query = Contact.query.order_by(Contact.id.desc())
    else:
        fields = FieldDefinition.query.filter_by(is_visible=True).order_by(FieldDefinition.field_order).all()
        query = Contact.query.filter_by(is_visible=True).order_by(Contact.id.desc())

    if search and fields:
        from ...models.contact import ContactValue
        matching_ids = (
            ContactValue.query
            .filter(ContactValue.value.ilike(f'%{search}%'))
            .with_entities(ContactValue.contact_id)
            .distinct()
        )
        query = query.filter(Contact.id.in_(matching_ids))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    contacts = pagination.items

    return render_template('contacts/index.html',
                           contacts=contacts,
                           fields=fields,
                           pagination=pagination,
                           search=search)


@contacts_bp.route('/contact/<int:contact_id>')
@login_required
def detail(contact_id):
    contact = Contact.query.get_or_404(contact_id)

    if not current_user.is_admin and not contact.is_visible:
        return redirect(url_for('contacts.index'))

    if current_user.is_admin:
        fields = FieldDefinition.query.order_by(FieldDefinition.field_order).all()
    else:
        fields = FieldDefinition.query.filter_by(is_visible=True).order_by(FieldDefinition.field_order).all()

    return render_template('contacts/detail.html', contact=contact, fields=fields)
