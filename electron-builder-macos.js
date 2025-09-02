module.exports = {
  appId: "com.accuratemachinerepair.maintenance.tracker",
  productName: "Accurate Machine Repair Maintenance Tracker",
  directories: {
    output: "dist"
  },
  mac: {
    target: [
      {
        target: "dmg",
        arch: ["arm64"]
      },
      {
        target: "dmg", 
        arch: ["x64"]
      }
    ],
    artifactName: "Accurate-Machine-Repair-Maintenance-Tracker-macOS-${arch}-${version}.${ext}",
    icon: "assets/icon.icns"
  },
  dmg: {
  },
  asarUnpack: [
    "package.json",
    "app-package.json",
    "latest.yml",
    "versions.json",
    "**/*.py",
    "requirements.txt"
  ],
  files: [
    "main.js",
    "preload.js",
    "splash-preload.js",
    "app.py",
    "package.json",
    "app-package.json",
    "latest.yml",
    "versions.json",
    "requirements.txt",
    "config.py",
    "models.py",
    "sqlalchemy_datetime_patch.py",
    "timezone_utils.py",
    "sync_utils_enhanced.py",
    "security_event_batcher.py",
    "security_event_logger.py",
    "load_bootstrap_env.py",
    "auto_migrate.py",
    "excel_importer.py",
    "schema_validator.py",
    "cache_config.py",
    "db_config.py",
    "db_utils.py",
    "api_endpoints.py",
    "sync_utils.py",
    "datetime_utils.py",
    "migrate_app_settings.py",
    "add_sync_queue_table.py",
    "notification_scheduler.py",
    "sqlite_schema_migration.py",
    "import_excel.py",
    "templates/**/*",
    "static/**/*",
    "assets/**/*",
    "view-logs.bat",
    "install-dependencies.bat",
    "node_modules/**/*",
    "!node_modules/.cache",
    "!**/node_modules/*/{CHANGELOG.md,README.md,README,readme.md,readme}",
    "!**/node_modules/*/{test,__tests__,tests,powered-test,example,examples}",
    "!**/node_modules/*.d.ts",
    "!**/node_modules/.bin",
    "!**/*.{iml,o,hprof,orig,pyc,pyo,rbc,swp,csproj,sln,xproj}",
    "!.editorconfig",
    "!**/._*",
    "!**/{.DS_Store,.git,.hg,.svn,CVS,RCS,SCCS,.gitignore,.gitattributes}",
    "!**/{__pycache__,thumbs.db,.flowconfig,.idea,.vs,.nyc_output}",
    "!**/{appveyor.yml,.travis.yml,circle.yml}",
    "!**/{npm-debug.log,yarn.lock,.yarn-integrity,.yarn-metadata.json}"
  ],
  asarUnpack: [
    "app.py",
    "config.py", 
    "models.py",
    "sqlalchemy_datetime_patch.py",
    "timezone_utils.py",
    "sync_utils_enhanced.py",
    "security_event_batcher.py",
    "security_event_logger.py",
    "load_bootstrap_env.py",
    "auto_migrate.py",
    "excel_importer.py",
    "schema_validator.py",
    "cache_config.py",
    "db_config.py",
    "db_utils.py",
    "api_endpoints.py",
    "sync_utils.py",
    "datetime_utils.py",
    "migrate_app_settings.py",
    "add_sync_queue_table.py",
    "notification_scheduler.py",
    "sqlite_schema_migration.py",
    "import_excel.py",
    "requirements.txt",
    "templates/**/*",
    "static/**/*"
  ],
  extraResources: [
    {
      from: "macos-python/python",
      to: "python",
      filter: ["**/*"]
    }
  ]
};
