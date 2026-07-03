import { useNavigate } from "react-router-dom";

function LoginForm() {
  const navigate = useNavigate();

  return (
    <div
      className="card shadow p-4"
      style={{ maxWidth: "400px", width: "100%" }}
    >
      <h2 className="text-center mb-4">HydroSense Lab Portal</h2>

      <div className="mb-3">
        <label className="form-label">Email</label>
        <input
          type="email"
          className="form-control"
          placeholder="Enter your email"
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Password</label>
        <input
          type="password"
          className="form-control"
          placeholder="Enter your password"
        />
      </div>

      <button
        className="btn btn-primary w-100"
        onClick={() => navigate("/dashboard")}
      >
        Login
      </button>
    </div>
  );
}

export default LoginForm;