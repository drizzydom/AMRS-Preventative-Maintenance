import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [maintenanceRecords, setMaintenanceRecords] = useState([]);
  const [newRecord, setNewRecord] = useState({ machine: '', part: '', description: '', date: '' });

  useEffect(() => {
    fetchMaintenanceRecords();
  }, []);

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
          <li key={record.id}>{record.machine} - {record.part} - {record.description} - {record.date}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
