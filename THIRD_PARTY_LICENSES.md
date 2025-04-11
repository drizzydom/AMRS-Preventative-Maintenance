# Third-Party Software Licenses

This document contains license and notice information for third-party software included with AMRS Preventative Maintenance System.

## Node.js Dependencies

### electron
- **License**: MIT
- **Repository**: https://github.com/electron/electron

### electron-builder
- **License**: MIT
- **Repository**: https://github.com/electron-userland/electron-builder

### electron-updater
- **License**: MIT
- **Repository**: https://github.com/electron-userland/electron-builder

### electron-log
- **License**: MIT
- **Repository**: https://github.com/megahertz/electron-log

### canvas
- **License**: MIT
- **Repository**: https://github.com/Automattic/node-canvas

### icon-gen
- **License**: MIT
- **Repository**: https://github.com/akabekobeko/npm-icon-gen

## Python Dependencies

### Flask
- **License**: BSD 3-Clause
- **Repository**: https://github.com/pallets/flask

### SQLAlchemy
- **License**: MIT
- **Repository**: https://github.com/sqlalchemy/sqlalchemy

### pandas
- **License**: BSD 3-Clause
- **Repository**: https://github.com/pandas-dev/pandas

### openpyxl
- **License**: MIT
- **Repository**: https://openpyxl.readthedocs.io/

### Werkzeug
- **License**: BSD 3-Clause
- **Repository**: https://github.com/pallets/werkzeug

### Jinja2
- **License**: BSD 3-Clause
- **Repository**: https://github.com/pallets/jinja

## Frontend Libraries

### Bootstrap
- **License**: MIT
- **Repository**: https://github.com/twbs/bootstrap

### Font Awesome
- **License**: Font Awesome Free License (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License)
- **Repository**: https://github.com/FortAwesome/Font-Awesome

## Note on Completing the Audit

This document requires completion through the following steps:

1. Run `npm list --json` and analyze all dependencies
2. Run `pip list --format=json` and analyze all Python dependencies
3. Review all third-party assets (images, fonts, etc.)
4. Check inline code for attribution requirements

The current list is based on visible dependencies in the README and may be incomplete.
