import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Loading() {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/dashboard");
    }, 3000);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div
      className="container-fluid d-flex justify-content-center align-items-center"
      style={{ minHeight: "100vh", backgroundColor: "#f8f9fa" }}
    >
      <div className="text-center">

        <div className="spinner-border text-primary mb-4" role="status"></div>

        <h2>Starting Your Lab...</h2>

        <p className="text-muted">
          Provisioning your container. Please wait...
        </p>

      </div>
    </div>
  );
}

export default Loading;