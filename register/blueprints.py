# Import every blueprint file
from register.views import general, item, items, entry, record, proof, register, entries, records, proofs


def register_blueprints(app):
    # Adds all blueprint objects into the app.
    app.register_blueprint(general.general)
    app.register_blueprint(item.item, url_prefix='/item')
    app.register_blueprint(items.items, url_prefix='/items')
    app.register_blueprint(entry.entry, url_prefix='/entry')
    app.register_blueprint(entries.entries, url_prefix='/entries')
    app.register_blueprint(record.record, url_prefix='/record')
    app.register_blueprint(records.records, url_prefix='/records')
    app.register_blueprint(proof.proof, url_prefix='/proof')
    app.register_blueprint(proofs.proofs, url_prefix='/proofs')
    app.register_blueprint(register.register_blueprint, url_prefix='/register')
    # All done!
    app.logger.info("Blueprints registered")
