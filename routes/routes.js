const express = require('express');
const router = express.Router();
const { checkPermission, isAuthenticated } = require('../middleware/authMiddleware');
const machineController = require('../controllers/machineController');
const partController = require('../controllers/partController');
const siteController = require('../controllers/siteController');
const userController = require('../controllers/userController');
const maintenanceController = require('../controllers/maintenanceController');
const permissions = require('../config/permissions');

// Machine routes
router.post('/machines', isAuthenticated, checkPermission(permissions.MACHINE.ADD), machineController.addMachine);
router.get('/machines', isAuthenticated, machineController.getAllMachines);
router.get('/machines/:id', isAuthenticated, machineController.getMachineById);
router.put('/machines/:id', isAuthenticated, checkPermission(permissions.MACHINE.MODIFY), machineController.modifyMachine);
router.delete('/machines/:id', isAuthenticated, checkPermission(permissions.MACHINE.DELETE), machineController.deleteMachine);

// Part routes
router.post('/parts', isAuthenticated, checkPermission(permissions.PART.ADD), partController.addPart);
router.get('/parts', isAuthenticated, partController.getAllParts);
router.get('/parts/:id', isAuthenticated, partController.getPartById);
router.put('/parts/:id', isAuthenticated, checkPermission(permissions.PART.MODIFY), partController.modifyPart);
router.delete('/parts/:id', isAuthenticated, checkPermission(permissions.PART.DELETE), partController.deletePart);

// Site routes
router.post('/sites', isAuthenticated, checkPermission(permissions.SITE.ADD), siteController.addSite);
router.get('/sites', isAuthenticated, siteController.getAllSites);
router.get('/sites/:id', isAuthenticated, siteController.getSiteById);
router.put('/sites/:id', isAuthenticated, checkPermission(permissions.SITE.MODIFY), siteController.modifySite);
router.delete('/sites/:id', isAuthenticated, checkPermission(permissions.SITE.DELETE), siteController.deleteSite);

// User routes
router.post('/users', isAuthenticated, checkPermission(permissions.USER.ADD), userController.addUser);
router.get('/users', isAuthenticated, userController.getAllUsers);
router.get('/users/:id', isAuthenticated, userController.getUserById);
router.put('/users/:id', isAuthenticated, checkPermission(permissions.USER.MODIFY), userController.modifyUser);
router.delete('/users/:id', isAuthenticated, checkPermission(permissions.USER.DELETE), userController.deleteUser);

// Maintenance routes
router.post('/maintenance', isAuthenticated, checkPermission(permissions.MAINTENANCE.ADD), maintenanceController.addMaintenanceRecord);
router.get('/maintenance', isAuthenticated, maintenanceController.getAllMaintenanceRecords);
router.get('/maintenance/:id', isAuthenticated, maintenanceController.getMaintenanceRecordById);
router.put('/maintenance/:id', isAuthenticated, checkPermission(permissions.MAINTENANCE.MODIFY), maintenanceController.modifyMaintenanceRecord);
router.delete('/maintenance/:id', isAuthenticated, checkPermission(permissions.MAINTENANCE.DELETE), maintenanceController.deleteMaintenanceRecord);

module.exports = router;
