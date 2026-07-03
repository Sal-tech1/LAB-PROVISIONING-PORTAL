import { Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Loading from "./pages/Loading";

function App() {
  return (
    <Routes>

      <Route path="/" element={<Login />} />

      <Route path="/login" element={<Login />} />

      <Route path="/dashboard" element={<Dashboard />} />

      <Route path="/loading" element={<Loading />} />

    </Routes>
  );
}

export default App;