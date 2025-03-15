import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import Navbar from './Navbar';
import Login from './Login';
import AdminPanel from './AdminPanel';
import './App.css';

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [maintenanceRecords, setMaintenanceRecords] = useState([]);
  const [newRecord, setNewRecord] = useState({ machine: '', part: '', description: '', date: '' });
  const [machines, setMachines] = useState([]);
  const [expandedMachines, setExpandedMachines] = useState({});

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      setLoggedIn(true);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (loggedIn) {
      fetchMaintenanceRecords();
      generateDummyData();
    }
  }, [loggedIn]);

  // Add authentication header to axios requests
  axios.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      if (userId) {
        config.headers['User-ID'] = userId;
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  const handleLogout = () => {
    // Clear auth data
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('isAdmin');
    setLoggedIn(false);
  };

  const fetchMaintenanceRecords = async () => {
    const response = await axios.get('http://localhost:5001/maintenance');
    setMaintenanceRecords(response.data);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewRecord({ ...newRecord, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:5001/maintenance', newRecord);
    fetchMaintenanceRecords();
  };

  const handleDelete = async (id) => {
    await axios.delete(`http://localhost:5001/maintenance/${id}`);
    fetchMaintenanceRecords();
  };

  const generateDummyData = () => {
    const dummyMachines = [];
    for (let i = 1; i <= 4; i++) {
      const parts = [];
      const numParts = Math.floor(Math.random() * 15) + 1;
      for (let j = 1; j <= numParts; j++) {
        const lastMaintenanceDate = new Date();
        lastMaintenanceDate.setDate(lastMaintenanceDate.getDate() - Math.floor(Math.random() * 30));
        const nextMaintenanceDate = new Date(lastMaintenanceDate);
        nextMaintenanceDate.setDate(lastMaintenanceDate.getDate() + 30);
        parts.push({
          id: j,
          name: `Part ${j}`,
          lastMaintenanceDate: lastMaintenanceDate.toISOString().split('T')[0],
          nextMaintenanceDate: nextMaintenanceDate.toISOString().split('T')[0]
        });
      }
      dummyMachines.push({
        id: i,
        name: `Machine ${i}`,
        parts: parts.sort((a, b) => new Date(a.nextMaintenanceDate) - new Date(b.nextMaintenanceDate))
      });
    }
    setMachines(dummyMachines);
  };

  const getColorForDate = (date) => {
    const today = new Date();
    const targetDate = new Date(date);
    const diffTime = Math.abs(targetDate - today);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 7) {
      return 'red';
    } else if (diffDays <= 14) {
      return 'orange';
    } else {
      return 'green';
    }
  };

  const toggleMachine = (id) => {
    setExpandedMachines(prevState => ({
      ...prevState,
      [id]: !prevState[id]
    }));
  };

  if (loading) {
    return <div className="container text-center mt-5"><h2>Loading...</h2></div>;
  }

  if (!loggedIn) {
    return <Login setLoggedIn={setLoggedIn} />;
  }

  return (
    <Router>
      <Navbar onLogout={handleLogout} />
      <div className="container">
        <Switch>
          <Route path="/" exact>
            <h1 className="text-center">Maintenance Tracker</h1>
            <div className="row">
              <div className="col-md-3">
                <div className="status-card blue">
                  <div className="status-icon">
                    <i className="fas fa-tasks"></i>
                  </div>
                  <div className="status-info">
                    <h3>104</h3>
                    <p>To Do</p>
                  </div>
                </div>
              </div>
              <div className="col-md-3">
                <div className="status-card orange">
                  <div className="status-icon">
                    <i className="fas fa-spinner"></i>
                  </div>
                  <div className="status-info">
                    <h3>1</h3>
                    <p>In Progress</p>
                  </div>
                </div>
              </div>
              <div className="col-md-3">
                <div className="status-card green">
                  <div className="status-icon">
                    <i className="fas fa-check"></i>
                  </div>
                  <div className="status-info">
                    <h3>4</h3>
                    <p>Done</p>
                  </div>
                </div>
              </div>
              <div className="col-md-3">
                <div className="status-card red">
                  <div className="status-icon">
                    <i className="fas fa-exclamation-triangle"></i>
                  </div>
                  <div className="status-info">
                    <h3>0</h3>
                    <p>My Open Assignments</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="row">
              {machines.map(machine => (
                <div key={machine.id} className="col-md-6 col-lg-4">
                  <div className="card">
                    <div className="card-header d-flex justify-content-between align-items-center">
                      <h2 className="mb-0">{machine.name}</h2>
                      <button className="toggle-button" onClick={() => toggleMachine(machine.id)}>
                        {expandedMachines[machine.id] ? 'Collapse' : 'Expand'}
                      </button>
                    </div>
                    {expandedMachines[machine.id] && (
                      <div className="card-body">
                        <ul>
                          {machine.parts.map(part => (
                            <li key={part.id} style={{ color: getColorForDate(part.nextMaintenanceDate) }}>
                              {part.name} - Last Maintenance: {part.lastMaintenanceDate} - Next Maintenance: {part.nextMaintenanceDate}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Route>
          <Route path="/add">
            <h1 className="text-center">Add Maintenance Record</h1>
            <form onSubmit={handleSubmit} className="form-group">
              <input type="text" name="machine" placeholder="Machine" value={newRecord.machine} onChange={handleInputChange} className="form-control" />
              <input type="text" name="part" placeholder="Part" value={newRecord.part} onChange={handleInputChange} className="form-control" />
              <input type="text" name="description" placeholder="Description" value={newRecord.description} onChange={handleInputChange} className="form-control" />
              <input type="date" name="date" value={newRecord.date} onChange={handleInputChange} className="form-control" />
              <button type="submit" className="btn btn-primary">Add Record</button>
            </form>
          </Route>
          <Route path="/view">
            <h1 className="text-center">View Maintenance Records</h1>
            <ul className="list-group">
              {maintenanceRecords.map(record => (
                <li key={record.id} className="list-group-item d-flex justify-content-between align-items-center">
                  {record.machine} - {record.part} - {record.description} - {record.date}
                  <button onClick={() => handleDelete(record.id)} className="btn btn-danger">Delete</button>
                </li>
              ))}
            </ul>
          </Route>
          <Route path="/admin">
            <AdminPanel />
          </Route>
        </Switch>
      </div>
    </Router>
  );
}

export default App;
