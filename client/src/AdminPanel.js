import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import './App.css';

function AdminPanel() {
  const [sites, setSites] = useState([]);
  const [users, setUsers] = useState([]);
  const [machines, setMachines] = useState([]);
  const [parts, setParts] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [editingSite, setEditingSite] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [editingMachine, setEditingMachine] = useState(null);
  const [editingPart, setEditingPart] = useState(null);

  useEffect(() => {
    fetchCurrentUser();
    fetchSites();
    fetchUsers();
    fetchMachines();
    fetchParts();
    fetchRoles();
    fetchPermissions();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      // For demo, use the localStorage data instead of an API call
      const isAdmin = localStorage.getItem('isAdmin') === 'true';
      const username = localStorage.getItem('username');
      const userId = localStorage.getItem('userId');
      
      // Mock user data for testing
      setCurrentUser({
        id: userId,
        username: username,
        isAdmin: isAdmin,
        permissions: isAdmin ? 
          Object.values(permissions).flatMap(category => Object.values(category)) : []
      });
    } catch (error) {
      console.error('Error fetching current user:', error);
      // Avoid infinite redirect loop by not redirecting here
    }
  };

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
    try {
      const name = e.target.elements.name.value;
      await axios.post('http://localhost:5001/sites', 
        { name }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchSites();
      e.target.reset();
    } catch (error) {
      console.error('Error adding site:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add sites');
      }
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      const username = e.target.elements.username.value;
      const password = e.target.elements.password.value;
      const role_id = e.target.elements.role_id.value;
      await axios.post('http://localhost:5001/users', 
        { username, password, role_id }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchUsers();
      e.target.reset();
    } catch (error) {
      console.error('Error adding user:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add users');
      }
    }
  };

  const handleAddMachine = async (e) => {
    e.preventDefault();
    try {
      const name = e.target.elements.name.value;
      const site_id = e.target.elements.site_id.value;
      await axios.post('http://localhost:5001/machines', 
        { name, site_id }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchMachines();
      e.target.reset();
    } catch (error) {
      console.error('Error adding machine:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add machines');
      }
    }
  };

  const handleAddPart = async (e) => {
    e.preventDefault();
    try {
      const name = e.target.elements.name.value;
      const machine_id = e.target.elements.machine_id.value;
      await axios.post('http://localhost:5001/parts', 
        { name, machine_id }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchParts();
      e.target.reset();
    } catch (error) {
      console.error('Error adding part:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add parts');
      }
    }
  };

  const handleAddRole = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    await axios.post('http://localhost:5001/roles', { name }, { headers: { 'User-ID': currentUser.id } });
    fetchRoles();
  };

  const handleAddPermission = async (e) => {
    e.preventDefault();
    const name = e.target.elements.name.value;
    const role_id = e.target.elements.role_id.value;
    await axios.post('http://localhost:5001/permissions', { name, role_id }, { headers: { 'User-ID': currentUser.id } });
    fetchPermissions();
  };

  const handleDeleteSite = async (id) => {
    try {
      await axios.delete(`http://localhost:5001/sites/${id}`, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchSites();
    } catch (error) {
      console.error('Error deleting site:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete sites');
      }
    }
  };

  const handleEditSite = (site) => {
    setEditingSite(site);
  };

  const handleUpdateSite = async (e) => {
    e.preventDefault();
    try {
      const name = e.target.elements.name.value;
      await axios.put(`http://localhost:5001/sites/${editingSite.id}`, 
        { name }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      setEditingSite(null);
      fetchSites();
    } catch (error) {
      console.error('Error updating site:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify sites');
      }
    }
  };

  const handleDeleteUser = async (id) => {
    try {
      await axios.delete(`http://localhost:5001/users/${id}`, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete users');
      }
    }
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const username = e.target.elements.username.value;
      const role_id = e.target.elements.role_id.value;
      const password = e.target.elements.password.value;
      
      const userData = { 
        username, 
        role_id
      };
      
      if (password) {
        userData.password = password;
      }
      
      await axios.put(`http://localhost:5001/users/${editingUser.id}`, 
        userData, 
        { headers: { 'User-ID': currentUser.id } }
      );
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify users');
      }
    }
  };

  const handleDeleteMachine = async (id) => {
    try {
      await axios.delete(`http://localhost:5001/machines/${id}`, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchMachines();
    } catch (error) {
      console.error('Error deleting machine:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete machines');
      }
    }
  };

  const handleEditMachine = (machine) => {
    setEditingMachine(machine);
  };

  const handleUpdateMachine = async (e) => {
    e.preventDefault();
    try {
      const name = e.target.elements.name.value;
      const site_id = e.target.elements.site_id.value;
      await axios.put(`http://localhost:5001/machines/${editingMachine.id}`, 
        { name, site_id }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      setEditingMachine(null);
      fetchMachines();
    } catch (error) {
      console.error('Error updating machine:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify machines');
      }
    }
  };

  const handleDeletePart = async (id) => {
    try {
      await axios.delete(`http://localhost:5001/parts/${id}`, 
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchParts();
    } catch (error) {
      console.error('Error deleting part:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete parts');
      }
    }
  };

  const handleEditPart = (part) => {
    setEditingPart(part);
  };

  const handleUpdatePart = async (e) => {
    e.preventDefault();
    try {
      const name = e.target.elements.name.value;
      const machine_id = e.target.elements.machine_id.value;
      await axios.put(`http://localhost:5001/parts/${editingPart.id}`, 
        { name, machine_id }, 
        { headers: { 'User-ID': currentUser.id } }
      );
      setEditingPart(null);
      fetchParts();
    } catch (error) {
      console.error('Error updating part:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify parts');
      }
    }
  };

  return (
    <div className="container">
      <h1 className="text-center">Admin Panel</h1>
      {!currentUser && <p className="alert alert-warning">Loading user data...</p>}
      {currentUser && !currentUser.isAdmin && (
        <p className="alert alert-danger">
          You do not have administrator permissions to access this page.
        </p>
      )}
      
      {currentUser && currentUser.isAdmin && (
        <>
          <div className="row">
            <div className="col-md-6">
              <h2>Sites</h2>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.SITE.ADD)) && (
                <form onSubmit={handleAddSite}>
                  <input type="text" name="name" placeholder="Site Name" className="form-control" />
                  <button type="submit" className="btn btn-primary">Add Site</button>
                </form>
              )}
              {editingSite && (
                <form onSubmit={handleUpdateSite}>
                  <input 
                    type="text" 
                    name="name" 
                    placeholder="Site Name" 
                    className="form-control" 
                    defaultValue={editingSite.name}
                  />
                  <div>
                    <button type="submit" className="btn btn-success">Update</button>
                    <button 
                      type="button" 
                      className="btn btn-secondary" 
                      onClick={() => setEditingSite(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
              <ul className="list-group">
                {sites.map(site => (
                  <li key={site.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/sites/${site.id}`}>{site.name}</Link>
                    <div>
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('site:modify')) && (
                        <button 
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditSite(site)}
                        >
                          Edit
                        </button>
                      )}
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('site:delete')) && (
                        <button 
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeleteSite(site.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="col-md-6">
              <h2>Users</h2>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.USER.ADD)) && (
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
              )}
              {editingUser && (
                <form onSubmit={handleUpdateUser}>
                  <input 
                    type="text" 
                    name="username" 
                    placeholder="Username" 
                    className="form-control" 
                    defaultValue={editingUser.username}
                  />
                  <input 
                    type="password" 
                    name="password" 
                    placeholder="Password" 
                    className="form-control" 
                  />
                  <select name="role_id" className="form-control" defaultValue={editingUser.role_id}>
                    {roles.map(role => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}
                  </select>
                  <div>
                    <button type="submit" className="btn btn-success">Update</button>
                    <button 
                      type="button" 
                      className="btn btn-secondary" 
                      onClick={() => setEditingUser(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
              <ul className="list-group">
                {users.map(user => (
                  <li key={user.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/users/${user.id}`}>{user.username}</Link>
                    <div>
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('user:modify')) && (
                        <button 
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditUser(user)}
                        >
                          Edit
                        </button>
                      )}
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('user:delete')) && (
                        <button 
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeleteUser(user.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="row">
            <div className="col-md-6">
              <h2>Machines</h2>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.MACHINE.ADD)) && (
                <form onSubmit={handleAddMachine}>
                  <input type="text" name="name" placeholder="Machine Name" className="form-control" />
                  <select name="site_id" className="form-control">
                    {sites.map(site => (
                      <option key={site.id} value={site.id}>{site.name}</option>
                    ))}
                  </select>
                  <button type="submit" className="btn btn-primary">Add Machine</button>
                </form>
              )}
              {editingMachine && (
                <form onSubmit={handleUpdateMachine}>
                  <input 
                    type="text" 
                    name="name" 
                    placeholder="Machine Name" 
                    className="form-control" 
                    defaultValue={editingMachine.name}
                  />
                  <select name="site_id" className="form-control" defaultValue={editingMachine.site_id}>
                    {sites.map(site => (
                      <option key={site.id} value={site.id}>{site.name}</option>
                    ))}
                  </select>
                  <div>
                    <button type="submit" className="btn btn-success">Update</button>
                    <button 
                      type="button" 
                      className="btn btn-secondary" 
                      onClick={() => setEditingMachine(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
              <ul className="list-group">
                {machines.map(machine => (
                  <li key={machine.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/machines/${machine.id}`}>{machine.name}</Link>
                    <div>
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('machine:modify')) && (
                        <button 
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditMachine(machine)}
                        >
                          Edit
                        </button>
                      )}
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('machine:delete')) && (
                        <button 
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeleteMachine(machine.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="col-md-6">
              <h2>Parts</h2>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.PART.ADD)) && (
                <form onSubmit={handleAddPart}>
                  <input type="text" name="name" placeholder="Part Name" className="form-control" />
                  <select name="machine_id" className="form-control">
                    {machines.map(machine => (
                      <option key={machine.id} value={machine.id}>{machine.name}</option>
                    ))}
                  </select>
                  <button type="submit" className="btn btn-primary">Add Part</button>
                </form>
              )}
              {editingPart && (
                <form onSubmit={handleUpdatePart}>
                  <input 
                    type="text" 
                    name="name" 
                    placeholder="Part Name" 
                    className="form-control" 
                    defaultValue={editingPart.name}
                  />
                  <select name="machine_id" className="form-control" defaultValue={editingPart.machine_id}>
                    {machines.map(machine => (
                      <option key={machine.id} value={machine.id}>{machine.name}</option>
                    ))}
                  </select>
                  <div>
                    <button type="submit" className="btn btn-success">Update</button>
                    <button 
                      type="button" 
                      className="btn btn-secondary" 
                      onClick={() => setEditingPart(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
              <ul className="list-group">
                {parts.map(part => (
                  <li key={part.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/parts/${part.id}`}>{part.name}</Link>
                    <div>
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('part:modify')) && (
                        <button 
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditPart(part)}
                        >
                          Edit
                        </button>
                      )}
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('part:delete')) && (
                        <button 
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeletePart(part.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="row">
            <div className="col-md-6">
              <h2>Roles</h2>
              {currentUser && currentUser.permissions.includes('create_role') && (
                <form onSubmit={handleAddRole}>
                  <input type="text" name="name" placeholder="Role Name" className="form-control" />
                  <button type="submit" className="btn btn-primary">Add Role</button>
                </form>
              )}
              <ul className="list-group">
                {roles.map(role => (
                  <li key={role.id} className="list-group-item">
                    <Link to={`/roles/${role.id}`}>{role.name}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="col-md-6">
              <h2>Permissions</h2>
              {currentUser && currentUser.permissions.includes('create_permission') && (
                <form onSubmit={handleAddPermission}>
                  <input type="text" name="name" placeholder="Permission Name" className="form-control" />
                  <select name="role_id" className="form-control">
                    {roles.map(role => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}
                  </select>
                  <button type="submit" className="btn btn-primary">Add Permission</button>
                </form>
              )}
              <ul className="list-group">
                {permissions.map(permission => (
                  <li key={permission.id} className="list-group-item">
                    <Link to={`/permissions/${permission.id}`}>{permission.name}</Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default AdminPanel;
