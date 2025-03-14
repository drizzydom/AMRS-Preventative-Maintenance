import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './Login';

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [maintenanceRecords, setMaintenanceRecords] = useState([]);
  const [newRecord, setNewRecord] = useState({ machine: '', part: '', description: '', date: '' });
  const [editRecord, setEditRecord] = useState(null);

  useEffect(() => {
    if (loggedIn) {
      fetchMaintenanceRecords();
    }
  }, [loggedIn]);

  const fetchMaintenanceRecords = async () => {
    const response = await axios.get('http://localhost:5001/maintenance');
    setMaintenanceRecords(response.data);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewRecord({ ...newRecord, [name]: value });
  };

  const handleEditInputChange = (e) => {
    const { name, value } = e.target;
    setEditRecord({ ...editRecord, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:5001/maintenance', newRecord);
    fetchMaintenanceRecords();
    setNewRecord({ machine: '', part: '', description: '', date: '' });
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    await axios.put(`http://localhost:5001/maintenance/${editRecord.id}`, editRecord);
    fetchMaintenanceRecords();
    setEditRecord(null);
  };

  const handleDelete = async (id) => {
    await axios.delete(`http://localhost:5001/maintenance/${id}`);
    fetchMaintenanceRecords();
  };

  if (!loggedIn) {
    return <Login setLoggedIn={setLoggedIn} />;
  }

  return (
    <div>
      <h1>Maintenance Tracker</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="machine" placeholder="Machine" value={newRecord.machine} onChange={handleInputChange} />
        <input type="text" name="part" placeholder="Part" value={newRecord.part} onChange={handleInputChange} />
        <input type="text" name="description" placeholder="Description" value={newRecord.description} onChange={handleInputChange} />
        <input type="date" name="date" value={newRecord.date} onChange={handleInputChange} />
        <button type="submit">Add Record</button>
      </form>
      <ul>
        {maintenanceRecords.map(record => (
          <li key={record.id}>
            {record.machine} - {record.part} - {record.description} - {record.date}
            <button onClick={() => setEditRecord(record)}>Edit</button>
            <button onClick={() => handleDelete(record.id)}>Delete</button>
          </li>
        ))}
      </ul>
      {editRecord && (
        <form onSubmit={handleUpdate}>
          <input type="text" name="machine" placeholder="Machine" value={editRecord.machine} onChange={handleEditInputChange} />
          <input type="text" name="part" placeholder="Part" value={editRecord.part} onChange={handleEditInputChange} />
          <input type="text" name="description" placeholder="Description" value={editRecord.description} onChange={handleEditInputChange} />
          <input type="date" name="date" value={editRecord.date} onChange={handleEditInputChange} />
          <button type="submit">Update Record</button>
        </form>
      )}
    </div>
  );
}

export default App;
