import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import './App.css';

function AdminPanel() {ns configuration
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
  SITE: {
  useEffect(() => {,
    fetchCurrentUser();e',
    fetchSites();:modify'
    fetchUsers();
    fetchMachines();
    fetchParts();d',
    fetchRoles();:delete',
    fetchPermissions();y'
  }, []);
  MAINTENANCE: {
  const fetchCurrentUser = async () => {
    try {E: 'maintenance:delete',
      // For demo, use the localStorage data instead of an API call
      const isAdmin = localStorage.getItem('isAdmin') === 'true';
      const username = localStorage.getItem('username');
      const userId = localStorage.getItem('userId');
      on AdminPanel() {
      // Mock user data for testinge([]);
      setCurrentUser({rs] = useState([]);
        id: userId,setMachines] = useState([]);
        username: username, useState([]);
        isAdmin: isAdmin, = useState([]);
        permissions: isAdmin ? sions] = useState([]);
          Object.values(permissions).flatMap(category => Object.values(category)) : []
      });editingSite, setEditingSite] = useState(null);
    } catch (error) { setEditingUser] = useState(null);
      console.error('Error fetching current user:', error););
      // Avoid infinite redirect loop by not redirecting here
    }
  };eEffect(() => {
    fetchCurrentUser();
  const fetchSites = async () => {
    const response = await axios.get('http://localhost:5001/sites');
    setSites(response.data);
  };fetchParts();
    fetchRoles();
  const fetchUsers = async () => {
    const response = await axios.get('http://localhost:5001/users');
    setUsers(response.data);
  };nst fetchCurrentUser = async () => {
    try {
  const fetchMachines = async () => {ge data instead of an API call
    const response = await axios.get('http://localhost:5001/machines');
    setMachines(response.data);rage.getItem('username');
  };  const userId = localStorage.getItem('userId');
      
  const fetchParts = async () => {missions
    const response = await axios.get('http://localhost:5001/parts');
    setParts(response.data);sions).flatMap(category => Object.values(category)) : 
  };    []; // For non-admin users, we'd fetch their specific permissions from the server
      
  const fetchRoles = async () => {
    const response = await axios.get('http://localhost:5001/roles');
    setRoles(response.data);
  };    isAdmin: isAdmin,
        permissions: userPermissions
  const fetchPermissions = async () => {
    const response = await axios.get('http://localhost:5001/permissions');
    setPermissions(response.data);g current user:', error);
  };}
  };
  const handleAddSite = async (e) => {
    e.preventDefault();ync () => {
    try { response = await axios.get('http://localhost:5001/sites');
      const name = e.target.elements.name.value;
      await axios.post('http://localhost:5001/sites', 
        { name }, 
        { headers: { 'User-ID': currentUser.id } }
      );t response = await axios.get('http://localhost:5001/users');
      fetchSites();se.data);
      e.target.reset();
    } catch (error) {
      console.error('Error adding site:', error);
      if (error.response && error.response.status === 403) {machines');
        alert('You do not have permission to add sites');
      }
    }
  };nst fetchParts = async () => {
    const response = await axios.get('http://localhost:5001/parts');
  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      const username = e.target.elements.username.value;
      const password = e.target.elements.password.value;001/roles');
      const role_id = e.target.elements.role_id.value;
      await axios.post('http://localhost:5001/users', 
        { username, password, role_id }, 
        { headers: { 'User-ID': currentUser.id } }
      );t response = await axios.get('http://localhost:5001/permissions');
      fetchUsers();response.data);
      e.target.reset();
    } catch (error) {
      console.error('Error adding user:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add users');
      }onst name = e.target.elements.name.value;
    } await axios.post('http://localhost:5001/sites', 
  };    { name }, 
        { headers: { 'User-ID': currentUser.id } }
  const handleAddMachine = async (e) => {
    e.preventDefault();
    try {arget.reset();
      const name = e.target.elements.name.value;
      const site_id = e.target.elements.site_id.value;
      await axios.post('http://localhost:5001/machines', ) {
        { name, site_id }, ave permission to add sites');
        { headers: { 'User-ID': currentUser.id } }
      );
      fetchMachines();
      e.target.reset();
    } catch (error) { = async (e) => {
      console.error('Error adding machine:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add machines');
      }onst password = e.target.elements.password.value;
    } const role_id = e.target.elements.role_id.value;
  };  await axios.post('http://localhost:5001/users', 
        { username, password, role_id }, 
  const handleAddPart = async (e) => {tUser.id } }
    e.preventDefault();
    try {chUsers();
      const name = e.target.elements.name.value;
      const machine_id = e.target.elements.machine_id.value;
      await axios.post('http://localhost:5001/parts', 
        { name, machine_id }, ror.response.status === 403) {
        { headers: { 'User-ID': currentUser.id } }sers');
      );
      fetchParts();
      e.target.reset();
    } catch (error) {
      console.error('Error adding part:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to add parts');
      }onst name = e.target.elements.name.value;
    } const site_id = e.target.elements.site_id.value;
  };  await axios.post('http://localhost:5001/machines', 
        { name, site_id }, 
  const handleAddRole = async (e) => {tUser.id } }
    e.preventDefault();
    const name = e.target.elements.name.value;
    await axios.post('http://localhost:5001/roles', { name }, { headers: { 'User-ID': currentUser.id } });
    fetchRoles();r) {
  };  console.error('Error adding machine:', error);
      if (error.response && error.response.status === 403) {
  const handleAddPermission = async (e) => { add machines');
    e.preventDefault();
    const name = e.target.elements.name.value;
    const role_id = e.target.elements.role_id.value;
    await axios.post('http://localhost:5001/permissions', { name, role_id }, { headers: { 'User-ID': currentUser.id } });
    fetchPermissions(); async (e) => {
  };e.preventDefault();
    try {
  const handleDeleteSite = async (id) => {value;
    try {st machine_id = e.target.elements.machine_id.value;
      await axios.delete(`http://localhost:5001/sites/${id}`, 
        { headers: { 'User-ID': currentUser.id } }
      );{ headers: { 'User-ID': currentUser.id } }
      fetchSites();
    } catch (error) {
      console.error('Error deleting site:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete sites');
      }f (error.response && error.response.status === 403) {
    }   alert('You do not have permission to add parts');
  };  }
    }
  const handleEditSite = (site) => {
    setEditingSite(site);
  };nst handleAddRole = async (e) => {
    e.preventDefault();
  const handleUpdateSite = async (e) => {alue;
    e.preventDefault();ttp://localhost:5001/roles', { name }, { headers: { 'User-ID': currentUser.id } });
    try {Roles();
      const name = e.target.elements.name.value;
      await axios.put(`http://localhost:5001/sites/${editingSite.id}`, 
        { name }, ermission = async (e) => {
        { headers: { 'User-ID': currentUser.id } }
      );t name = e.target.elements.name.value;
      setEditingSite(null);t.elements.role_id.value;
      fetchSites();t('http://localhost:5001/permissions', { name, role_id }, { headers: { 'User-ID': currentUser.id } });
    } catch (error) {);
      console.error('Error updating site:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify sites');
      } {
    } await axios.delete(`http://localhost:5001/sites/${id}`, 
  };    { headers: { 'User-ID': currentUser.id } }
      );
  const handleDeleteUser = async (id) => {
    try {ch (error) {
      await axios.delete(`http://localhost:5001/users/${id}`, 
        { headers: { 'User-ID': currentUser.id } }=== 403) {
      );alert('You do not have permission to delete sites');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete users');
      }EditingSite(site);
    }
  };
  const handleUpdateSite = async (e) => {
  const handleEditUser = (user) => {
    setEditingUser(user);
  };  const name = e.target.elements.name.value;
      await axios.put(`http://localhost:5001/sites/${editingSite.id}`, 
  const handleUpdateUser = async (e) => {
    e.preventDefault();ser-ID': currentUser.id } }
    try {
      const username = e.target.elements.username.value;
      const role_id = e.target.elements.role_id.value;
      const password = e.target.elements.password.value;
      console.error('Error updating site:', error);
      const userData = { && error.response.status === 403) {
        username,  do not have permission to modify sites');
        role_id
      };
      
      if (password) {
        userData.password = password; => {
      } {
      await axios.delete(`http://localhost:5001/users/${id}`, 
      await axios.put(`http://localhost:5001/users/${editingUser.id}`, 
        userData, 
        { headers: { 'User-ID': currentUser.id } }
      );tch (error) {
      setEditingUser(null);deleting user:', error);
      fetchUsers();ponse && error.response.status === 403) {
    } catch (error) { not have permission to delete users');
      console.error('Error updating user:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify users');
      }
    }st handleEditUser = (user) => {
  };setEditingUser(user);
  };
  const handleDeleteMachine = async (id) => {
    try {andleUpdateUser = async (e) => {
      await axios.delete(`http://localhost:5001/machines/${id}`, 
        { headers: { 'User-ID': currentUser.id } }
      );nst username = e.target.elements.username.value;
      fetchMachines();e.target.elements.role_id.value;
    } catch (error) {= e.target.elements.password.value;
      console.error('Error deleting machine:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete machines');
      } role_id
    } };
  };  
      if (password) {
  const handleEditMachine = (machine) => {
    setEditingMachine(machine);
  };  
      await axios.put(`http://localhost:5001/users/${editingUser.id}`, 
  const handleUpdateMachine = async (e) => {
    e.preventDefault();ser-ID': currentUser.id } }
    try {
      const name = e.target.elements.name.value;
      const site_id = e.target.elements.site_id.value;
      await axios.put(`http://localhost:5001/machines/${editingMachine.id}`, 
        { name, site_id }, updating user:', error);
        { headers: { 'User-ID': currentUser.id } }=== 403) {
      );alert('You do not have permission to modify users');
      setEditingMachine(null);
      fetchMachines();
    } catch (error) {
      console.error('Error updating machine:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify machines');
      }wait axios.delete(`http://localhost:5001/machines/${id}`, 
    }   { headers: { 'User-ID': currentUser.id } }
  };  );
      fetchMachines();
  const handleDeletePart = async (id) => {
    try {sole.error('Error deleting machine:', error);
      await axios.delete(`http://localhost:5001/parts/${id}`, 
        { headers: { 'User-ID': currentUser.id } }e machines');
      );
      fetchParts();
    } catch (error) {
      console.error('Error deleting part:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to delete parts');
      }
    }
  };nst handleUpdateMachine = async (e) => {
    e.preventDefault();
  const handleEditPart = (part) => {
    setEditingPart(part);et.elements.name.value;
  };  const site_id = e.target.elements.site_id.value;
      await axios.put(`http://localhost:5001/machines/${editingMachine.id}`, 
  const handleUpdatePart = async (e) => {
    e.preventDefault();ser-ID': currentUser.id } }
    try {
      const name = e.target.elements.name.value;
      const machine_id = e.target.elements.machine_id.value;
      await axios.put(`http://localhost:5001/parts/${editingPart.id}`, 
        { name, machine_id }, ating machine:', error);
        { headers: { 'User-ID': currentUser.id } }=== 403) {
      );alert('You do not have permission to modify machines');
      setEditingPart(null);
      fetchParts();
    } catch (error) {
      console.error('Error updating part:', error);
      if (error.response && error.response.status === 403) {
        alert('You do not have permission to modify parts');
      }wait axios.delete(`http://localhost:5001/parts/${id}`, 
    }   { headers: { 'User-ID': currentUser.id } }
  };  );
      fetchParts();
  return (h (error) {
    <div className="container">ting part:', error);
      <h1 className="text-center">Admin Panel</h1>=== 403) {
      {!currentUser && <p className="alert alert-warning">Loading user data...</p>}
      {currentUser && !currentUser.isAdmin && (
        <p className="alert alert-danger">
          You do not have administrator permissions to access this page.
        </p>
      )}handleEditPart = (part) => {
      tEditingPart(part);
      {currentUser && currentUser.isAdmin && (
        <>
          <div className="row">c (e) => {
            <div className="col-md-6">
              <h2>Sites</h2>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.SITE.ADD)) && (
                <form onSubmit={handleAddSite}>ine_id.value;
                  <input type="text" name="name" placeholder="Site Name" className="form-control" />
                  <button type="submit" className="btn btn-primary">Add Site</button>
                </form>ser-ID': currentUser.id } }
              )}
              {editingSite && (
                <form onSubmit={handleUpdateSite}>
                  <input 
                    type="text" ing part:', error);
                    name="name" r.response.status === 403) {
                    placeholder="Site Name"  modify parts');
                    className="form-control" 
                    defaultValue={editingSite.name}
                  />
                  <div>
                    <button type="submit" className="btn btn-success">Update</button>
                    <button r">
                      type="button" min Panel</h1>
                      className="btn btn-secondary" ning">Loading user data...</p>}
                      onClick={() => setEditingSite(null)}
                    >"alert alert-danger">
                      Cancelministrator permissions to access this page.
                    </button>
                  </div>
                </form>
              )}er && currentUser.isAdmin && (
              <ul className="list-group">
                {sites.map(site => (
                  <li key={site.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/sites/${site.id}`}>{site.name}</Link>
                    <div>r && (currentUser.isAdmin || currentUser.permissions.includes(permissions.SITE.ADD)) && (
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.SITE.MODIFY)) && (
                        <button ext" name="name" placeholder="Site Name" className="form-control" />
                          className="btn btn-sm btn-primary mr-2" ">Add Site</button>
                          onClick={() => handleEditSite(site)}
                        >
                          Edit(
                        </button>andleUpdateSite}>
                      )} 
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.SITE.DELETE)) && (
                        <button 
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeleteSite(site.id)}
                        >ltValue={editingSite.name}
                          Delete
                        </button>
                      )}ton type="submit" className="btn btn-success">Update</button>
                    </div>n 
                  </li>ype="button" 
                ))}   className="btn btn-secondary" 
              </ul>   onClick={() => setEditingSite(null)}
            </div>  >
            <div className="col-md-6">
              <h2>Users</h2>>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.USER.ADD)) && (
                <form onSubmit={handleAddUser}>
                  <input type="text" name="username" placeholder="Username" className="form-control" />
                  <input type="password" name="password" placeholder="Password" className="form-control" />
                  <select name="role_id" className="form-control">
                    {roles.map(role => (sName="list-group-item d-flex justify-content-between align-items-center">
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}v>
                  </select>entUser && (currentUser.isAdmin || currentUser.permissions.includes('site:modify')) && (
                  <button type="submit" className="btn btn-primary">Add User</button>
                </form>   className="btn btn-sm btn-primary mr-2" 
              )}          onClick={() => handleEditSite(site)}
              {editingUser && (
                <form onSubmit={handleUpdateUser}>
                  <input /button>
                    type="text" 
                    name="username" & (currentUser.isAdmin || currentUser.permissions.includes('site:delete')) && (
                    placeholder="Username" 
                    className="form-control" sm btn-danger" 
                    defaultValue={editingUser.username}te(site.id)}
                  />    >
                  <input  Delete
                    type="password" 
                    name="password" 
                    placeholder="Password" 
                    className="form-control" 
                  />
                  <select name="role_id" className="form-control" defaultValue={editingUser.role_id}>
                    {roles.map(role => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}</h2>
                  </select>&& (currentUser.isAdmin || currentUser.permissions.includes(permissions.USER.ADD)) && (
                  <div>nSubmit={handleAddUser}>
                    <button type="submit" className="btn btn-success">Update</button>="form-control" />
                    <button e="password" name="password" placeholder="Password" className="form-control" />
                      type="button" _id" className="form-control">
                      className="btn btn-secondary" 
                      onClick={() => setEditingUser(null)}}>{role.name}</option>
                    >)}
                      Cancel
                    </button>e="submit" className="btn btn-primary">Add User</button>
                  </div>
                </form>
              )}ditingUser && (
              <ul className="list-group">ateUser}>
                {users.map(user => (
                  <li key={user.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/users/${user.id}`}>{user.username}</Link>
                    <div>holder="Username" 
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('user:modify')) && (
                        <button ={editingUser.username}
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditUser(user)}
                        >"password" 
                          Editword" 
                        </button>Password" 
                      )}sName="form-control" 
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('user:delete')) && (
                        <button role_id" className="form-control" defaultValue={editingUser.role_id}>
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeleteUser(user.id)}ame}</option>
                        >
                          Delete
                        </button>
                      )}ton type="submit" className="btn btn-success">Update</button>
                    </div>n 
                  </li>ype="button" 
                ))}   className="btn btn-secondary" 
              </ul>   onClick={() => setEditingUser(null)}
            </div>  >
          </div>      Cancel
          <div className="row">
            <div className="col-md-6">
              <h2>Machines</h2>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.MACHINE.ADD)) && (
                <form onSubmit={handleAddMachine}>
                  <input type="text" name="name" placeholder="Machine Name" className="form-control" />
                  <select name="site_id" className="form-control">lex justify-content-between align-items-center">
                    {sites.map(site => (user.id}`}>{user.username}</Link>
                      <option key={site.id} value={site.id}>{site.name}</option>
                    ))}currentUser && (currentUser.isAdmin || currentUser.permissions.includes('user:modify')) && (
                  </select>tton 
                  <button type="submit" className="btn btn-primary">Add Machine</button>
                </form>   onClick={() => handleEditUser(user)}
              )}        >
              {editingMachine && (
                <form onSubmit={handleUpdateMachine}>
                  <input 
                    type="text" er && (currentUser.isAdmin || currentUser.permissions.includes('user:delete')) && (
                    name="name" 
                    placeholder="Machine Name"  btn-danger" 
                    className="form-control" leDeleteUser(user.id)}
                    defaultValue={editingMachine.name}
                  />      Delete
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
                    >tUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.MACHINE.ADD)) && (
                      Cancelit={handleAddMachine}>
                    </button>="text" name="name" placeholder="Machine Name" className="form-control" />
                  </div>t name="site_id" className="form-control">
                </form>tes.map(site => (
              )}      <option key={site.id} value={site.id}>{site.name}</option>
              <ul className="list-group">
                {machines.map(machine => (
                  <li key={machine.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/machines/${machine.id}`}>{machine.name}</Link>
                    <div>
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('machine:modify')) && (
                        <button handleUpdateMachine}>
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditMachine(machine)}
                        >"name" 
                          Editr="Machine Name" 
                        </button>rm-control" 
                      )}ultValue={editingMachine.name}
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('machine:delete')) && (
                        <button site_id" className="form-control" defaultValue={editingMachine.site_id}>
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeleteMachine(machine.id)}option>
                        >
                          Delete
                        </button>
                      )}ton type="submit" className="btn btn-success">Update</button>
                    </div>n 
                  </li>ype="button" 
                ))}   className="btn btn-secondary" 
              </ul>   onClick={() => setEditingMachine(null)}
            </div>  >
            <div className="col-md-6">
              <h2>Parts</h2>>
              {currentUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.PART.ADD)) && (
                <form onSubmit={handleAddPart}>
                  <input type="text" name="name" placeholder="Part Name" className="form-control" />
                  <select name="machine_id" className="form-control">
                    {machines.map(machine => (
                      <option key={machine.id} value={machine.id}>{machine.name}</option>between align-items-center">
                    ))}nk to={`/machines/${machine.id}`}>{machine.name}</Link>
                  </select>
                  <button type="submit" className="btn btn-primary">Add Part</button>.includes('machine:modify')) && (
                </form> <button 
              )}          className="btn btn-sm btn-primary mr-2" 
              {editingPart && (ck={() => handleEditMachine(machine)}
                <form onSubmit={handleUpdatePart}>
                  <input  Edit
                    type="text" >
                    name="name" 
                    placeholder="Part Name" ntUser.isAdmin || currentUser.permissions.includes('machine:delete')) && (
                    className="form-control" 
                    defaultValue={editingPart.name}-danger" 
                  />      onClick={() => handleDeleteMachine(machine.id)}
                  <select name="machine_id" className="form-control" defaultValue={editingPart.machine_id}>
                    {machines.map(machine => (
                      <option key={machine.id} value={machine.id}>{machine.name}</option>
                    ))}}
                  </select>
                  <div>
                    <button type="submit" className="btn btn-success">Update</button>
                    <button 
                      type="button" 
                      className="btn btn-secondary" 
                      onClick={() => setEditingPart(null)}
                    >tUser && (currentUser.isAdmin || currentUser.permissions.includes(permissions.PART.ADD)) && (
                      Cancelit={handleAddPart}>
                    </button>="text" name="name" placeholder="Part Name" className="form-control" />
                  </div>t name="machine_id" className="form-control">
                </form>chines.map(machine => (
              )}      <option key={machine.id} value={machine.id}>{machine.name}</option>
              <ul className="list-group">
                {parts.map(part => (
                  <li key={part.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <Link to={`/parts/${part.id}`}>{part.name}</Link>
                    <div>
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('part:modify')) && (
                        <button handleUpdatePart}>
                          className="btn btn-sm btn-primary mr-2" 
                          onClick={() => handleEditPart(part)}
                        >"name" 
                          Editr="Part Name" 
                        </button>rm-control" 
                      )}ultValue={editingPart.name}
                      {currentUser && (currentUser.isAdmin || currentUser.permissions.includes('part:delete')) && (
                        <button machine_id" className="form-control" defaultValue={editingPart.machine_id}>
                          className="btn btn-sm btn-danger" 
                          onClick={() => handleDeletePart(part.id)}machine.name}</option>
                        >
                          Delete
                        </button>
                      )}ton type="submit" className="btn btn-success">Update</button>
                    </div>n 
                  </li>ype="button" 
                ))}   className="btn btn-secondary" 
              </ul>   onClick={() => setEditingPart(null)}
            </div>  >
          </div>      Cancel
          <div className="row">
            <div className="col-md-6">
              <h2>Roles</h2>
              {currentUser && currentUser.permissions.includes('create_role') && (
                <form onSubmit={handleAddRole}>
                  <input type="text" name="name" placeholder="Role Name" className="form-control" />
                  <button type="submit" className="btn btn-primary">Add Role</button>-between align-items-center">
                </form>nk to={`/parts/${part.id}`}>{part.name}</Link>
              )}    <div>
              <ul className="list-group">rrentUser.isAdmin || currentUser.permissions.includes('part:modify')) && (
                {roles.map(role => (
                  <li key={role.id} className="list-group-item">" 
                    <Link to={`/roles/${role.id}`}>{role.name}</Link>
                  </li> >
                ))}       Edit
              </ul>     </button>
            </div>    )}
            <div className="col-md-6">(currentUser.isAdmin || currentUser.permissions.includes('part:delete')) && (
              <h2>Permissions</h2>
              {currentUser && currentUser.permissions.includes('create_permission') && (
                <form onSubmit={handleAddPermission}>Part(part.id)}
                  <input type="text" name="name" placeholder="Permission Name" className="form-control" />
                  <select name="role_id" className="form-control">
                    {roles.map(role => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}iv>
                  </select>
                  <button type="submit" className="btn btn-primary">Add Permission</button>
                </form>
              )}v>
              <ul className="list-group">
                {permissions.map(permission => (
                  <li key={permission.id} className="list-group-item">
                    <Link to={`/permissions/${permission.id}`}>{permission.name}</Link>
                  </li>ser && currentUser.permissions.includes('create_role') && (
                ))}rm onSubmit={handleAddRole}>
              </ul>input type="text" name="name" placeholder="Role Name" className="form-control" />
            </div><button type="submit" className="btn btn-primary">Add Role</button>
          </div></form>
        </>   )}
      )}      <ul className="list-group">
    </div>      {roles.map(role => (
  );              <li key={role.id} className="list-group-item">
}                   <Link to={`/roles/${role.id}`}>{role.name}</Link>
                  </li>
export default AdminPanel;
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
