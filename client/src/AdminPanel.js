import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const PERMISSIONS = {
  MACHINE: {
    ADD: 'machine:add',
    DELETE: 'machine:delete',
    MODIFY: 'machine:modify'
  },
  PART: {
    ADD: 'part:add',
    DELETE: 'part:delete',
    MODIFY: 'part:modify'
  },
  SITE: {
    ADD: 'site:add',
    DELETE: 'site:delete',
    MODIFY: 'site:modify'
  },
  USER: {
    ADD: 'user:add',
    DELETE: 'user:delete',
    MODIFY: 'user:modify'
  }
};

function AdminPanel() {
  const [activeTab, setActiveTab] = useState('sites');
  const [data, setData] = useState({
    sites: [],
    machines: [],
    parts: [],
    users: [],
    roles: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const initializeAdmin = async () => {
      try {
        setLoading(true);
        await checkAdminAccess();
        await fetchAllData();
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    initializeAdmin();
  }, []);

  const checkAdminAccess = async () => {
    const isAdmin = localStorage.getItem('isAdmin') === 'true';
    const permissions = JSON.parse(localStorage.getItem('permissions') || '[]');
    
    if (!isAdmin && permissions.length === 0) {
      throw new Error('Access denied: Insufficient permissions');
    }

    setCurrentUser({
      isAdmin,
      permissions,
      username: localStorage.getItem('username')
    });
  };

  const fetchAllData = async () => {
    try {
      const [sites, machines, parts, users, roles] = await Promise.all([
        axios.get('http://localhost:5001/api/sites', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'User-ID': localStorage.getItem('userId')
          }
        }),
        axios.get('http://localhost:5001/api/machines', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'User-ID': localStorage.getItem('userId')
          }
        }),
        axios.get('http://localhost:5001/api/parts', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'User-ID': localStorage.getItem('userId')
          }
        }),
        axios.get('http://localhost:5001/api/users', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'User-ID': localStorage.getItem('userId')
          }
        }),
        axios.get('http://localhost:5001/api/roles', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'User-ID': localStorage.getItem('userId')
          }
        })
      ]);

      setData({
        sites: sites.data || [],
        machines: machines.data || [],
        parts: parts.data || [],
        users: users.data || [],
        roles: roles.data || []
      });
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch data. Please check your connection and permissions.');
      
      // Set empty arrays as fallback
      setData({
        sites: [],
        machines: [],
        parts: [],
        users: [],
        roles: []
      });
    }
  };

  const hasPermission = (permission) => {
    if (currentUser?.isAdmin) return true;
    return currentUser?.permissions.includes(permission);
  };

  if (loading) return <div className="text-center">Loading...</div>;
  if (error) return <div className="alert alert-danger">{error}</div>;

  return (
    <div className="admin-panel container mt-4">
      <h2 className="mb-4">Admin Panel</h2>
      
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'sites' ? 'active' : ''}`}
            onClick={() => setActiveTab('sites')}
          >
            Sites
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'machines' ? 'active' : ''}`}
            onClick={() => setActiveTab('machines')}
          >
            Machines
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'parts' ? 'active' : ''}`}
            onClick={() => setActiveTab('parts')}
          >
            Parts
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            Users
          </button>
        </li>
      </ul>

      <div className="tab-content">
        {activeTab === 'sites' && (
          <div className="tab-pane active">
            <h3>Sites Management</h3>
            {hasPermission(PERMISSIONS.SITE.ADD) && (
              <button className="btn btn-primary mb-3">Add Site</button>
            )}
            {data.sites.map(site => (
              <div key={site._id} className="card mb-2">
                <div className="card-body d-flex justify-content-between align-items-center">
                  <span>{site.name}</span>
                  <div>
                    {hasPermission(PERMISSIONS.SITE.MODIFY) && (
                      <button className="btn btn-sm btn-primary mr-2">Edit</button>
                    )}
                    {hasPermission(PERMISSIONS.SITE.DELETE) && (
                      <button className="btn btn-sm btn-danger">Delete</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'machines' && (
          <div className="tab-pane active">
            <h3>Machines Management</h3>
            {hasPermission(PERMISSIONS.MACHINE.ADD) && (
              <button className="btn btn-primary mb-3">Add Machine</button>
            )}
            {data.machines.map(machine => (
              <div key={machine._id} className="card mb-2">
                <div className="card-body d-flex justify-content-between align-items-center">
                  <span>{machine.name}</span>
                  <div>
                    {hasPermission(PERMISSIONS.MACHINE.MODIFY) && (
                      <button className="btn btn-sm btn-primary mr-2">Edit</button>
                    )}
                    {hasPermission(PERMISSIONS.MACHINE.DELETE) && (
                      <button className="btn btn-sm btn-danger">Delete</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'parts' && (
          <div className="tab-pane active">
            <h3>Parts Management</h3>
            {hasPermission(PERMISSIONS.PART.ADD) && (
              <button className="btn btn-primary mb-3">Add Part</button>
            )}
            {data.parts.map(part => (
              <div key={part._id} className="card mb-2">
                <div className="card-body d-flex justify-content-between align-items-center">
                  <span>{part.name}</span>
                  <div>
                    {hasPermission(PERMISSIONS.PART.MODIFY) && (
                      <button className="btn btn-sm btn-primary mr-2">Edit</button>
                    )}
                    {hasPermission(PERMISSIONS.PART.DELETE) && (
                      <button className="btn btn-sm btn-danger">Delete</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'users' && (
          <div className="tab-pane active">
            <h3>Users Management</h3>
            {hasPermission(PERMISSIONS.USER.ADD) && (
              <button className="btn btn-primary mb-3">Add User</button>
            )}
            {data.users.map(user => (
              <div key={user._id} className="card mb-2">
                <div className="card-body d-flex justify-content-between align-items-center">
                  <span>{user.username}</span>
                  <div>
                    {hasPermission(PERMISSIONS.USER.MODIFY) && (
                      <button className="btn btn-sm btn-primary mr-2">Edit</button>
                    )}
                    {hasPermission(PERMISSIONS.USER.DELETE) && (
                      <button className="btn btn-sm btn-danger">Delete</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminPanel;
