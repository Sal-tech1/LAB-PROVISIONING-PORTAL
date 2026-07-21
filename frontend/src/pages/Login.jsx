import LoginForm from "../components/LoginForm";

function Login() {
  return (
    <div
      className="container-fluid d-flex justify-content-center align-items-center"
      style={{ minHeight: "100vh", backgroundColor: "#f8f9fa" }}
    >
      <LoginForm />
    </div>
  );
}

export default Login;