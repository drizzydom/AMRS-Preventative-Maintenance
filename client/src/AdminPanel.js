import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function AdminPanel() {
  const [sites, setSites] = useState([]);
  const [users, setUsers] = useState([]);
  const [machines, setMachines] = useState([]);
  const [parts, setParts] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);

  useEffect(() => {
    fetchSites();
    fetchUsers();
    fetchMachines();
    fetchParts();
    fetchRoles();
    fetchPermissions();
  }, []);

  const fetchSites = async () => {
    const response = await axios.get('http://localhost:5001/sites');
    setSites(response.data);
  };

  const fetchUsers = async () => {
    const response = await axios.get('http://localhost:5001/users');
    setUsers(response.data);
  };

  const fetchMachines = async () => {
    const response = await axios.get('http://localhost:5001/machines');
    setMachines(response.data);
  };

  const fetchParts = async () => {
    const response = await axios.get('http://localhost:5001/parts');
    setParts(response.data);
  };

  const fetchRoles = async () => {
    const response = await axios.get('http://localhost:5001/roles');
    setRoles(response.data);
  };

  const fetchPermissions = async () => {
    const response = await axios.get('http://localhost:5001/permissions');
    setPermissions(response.data);
  };

  const handleAddSite = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    await axios.post('http://localhost:5001/sites', { name });
    fetchSites();
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    const username = e.target.elements.username.value;
    const password = e.target.elements.password.value;
    const role_id = e.target.elements.role_id.value;
    await axios.post('http://localhost:5001/users', { username, password, role_id });
    fetchUsers();
  };

  const handleAddMachine = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    const site_id = e.target.elements.site_id.value;
    await axios.post('http://localhost:5001/machines', { name, site_id });
    fetchMachines();
  };

  const handleAddPart = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    const machine_id = e.target.elements.machine_id.value;
    await axios.post('http://localhost:5001/parts', { name, machine_id });
    fetchParts();
  };

  const handleAddRole = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    await axios.post('http://localhost:5001/roles', { name });
    fetchRoles();
  };

  const handleAddPermission = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    const role_id = e.target.elements.role_id.value;
    await axios.post('http://localhost:5001/permissions', { name, role_id });
    fetchPermissions();
  };

  return (
    <div className="container">
      <h1 className="text-center">Admin Panel</h1>
      <div className="row">
        <div className="col-md-6">
          <h2>Sites</h2>
          <form onSubmit={handleAddSite}>
            <input type="text" name="name" placeholder="Site Name" className="form-control" />
            <button type="submit" className="btn btn-primary">Add Site</button>
          </form>
          <ul className="list-group">
            {sites.map(site => (
              <li key={site.id} className="list-group-item">{site.name}</li>
            ))}
          </ul>
        </div>
        <div className="col-md-6">
          <h2>Users</h2>
          <form onSubmit={handleAddUser}>
            <input type="text" name="username" placeholder="Username" className="form-control" />
            <input type="password" name="password" placeholder="Password" className="form-control" />
            <select name="role_id" className="form-control">
              {roles.map(role => (
                <option key={role.id} value={role.id}>{role.name}</option>
              ))}
            </select>
            <button type="submit" className="btn btn-primary">Add User</button>
          </form>
          <ul className="list-group">
            {users.map(user => (
              <li key={user.id} className="list-group-item">{user.username}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="row">
        <div className="col-md-6">
          <h2>Machines</h2>
          <form onSubmit={handleAddMachine}>
            <input type="text" name="name" placeholder="Machine Name" className="form-control" />
            <select name="site_id" className="form-control">
              {sites.map(site => (
                <option key={site.id} value={site.id}>{site.name}</option>
              ))}
            </select>
            <button type="submit" className="btn btn-primary">Add Machine</button>
          </form>
          <ul className="list-group">
            {machines.map(machine => (
              <li key={machine.id} className="list-group-item">{machine.name}</li>
            ))}
          </ul>
        </div>
        <div className="col-md-6">
          <h2>Parts</h2>
          <form onSubmit={handleAddPart}>
            <input type="text" name="name" placeholder="Part Name" className="form-control" />
            <select name="machine_id" className="form-control">
              {machines.map(machine => (
                <option key={machine.id} value={machine.id}>{machine.name}</option>
              ))}
            </select>
            <button type="submit" className="btn btn-primary">Add Part</button>
          </form>
          <ul className="list-group">
            {parts.map(part => (
              <li key={part.id} className="list-group-item">{part.name}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="row">
        <div className="col-md-6">
          <h2>Roles</h2>
          <form onSubmit={handleAddRole}>
            <input type="text" name="name" placeholder="Role Name" className="form-control" />
            <button type="submit" className="btn btn-primary">Add Role</button>
          </form>
          <ul className="list-group">
            {roles.map(role => (
              <li key={role.id} className="list-group-item">{role.name}</li>
            ))}
          </ul>
        </div>
        <div className="col-md-6">
          <h2>Permissions</h2>
          <form onSubmit={handleAddPermission}>
            <input type="text" name="name" placeholder="Permission Name" className="form-control" />
            <select name="role_id" className="form-control">
              {roles.map(role => (
                <option key={role.id} value={role.id}>{role.name}</option>
              ))}
            </select>
            <button type="submit" className="btn btn-primary">Add Permission</button>
          </form>
          <ul className="list-group">
            {permissions.map(permission => (
              <li key={permission.id} className="list-group-item">{permission.name}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;
