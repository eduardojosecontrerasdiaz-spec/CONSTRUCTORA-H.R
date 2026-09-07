export function LoginPage() {
  return (
    <div>
      {/* LOGIN */}
      <h2>Login</h2>

      <form>
        <div>
          <input type="text" placeholder="Username" />
          <span>👤</span>
        </div>

        <div>
          <input type="password" placeholder="Password" />
          <span>🔒</span>
        </div>

        <a href="#">Forgot Password?</a>
        <br />

        <button type="submit">Login</button>
      </form>

      <p>or login with social platforms</p>

      <div>
        <a href="#">G</a>
        <a href="#">f</a>
        <a href="#">◎</a>
        <a href="#">in</a>
      </div>

      {/* REGISTRATION */}
      <h2>Registration</h2>

      <form>
        <div>
          <input type="text" placeholder="Username" />
          <span>👤</span>
        </div>

        <div>
          <input type="email" placeholder="Email" />
          <span>✉</span>
        </div>

        <div>
          <input type="password" placeholder="Password" />
          <span>🔒</span>
        </div>

        <button type="submit">Register</button>
      </form>

      <p>or register with social platforms</p>

      <div>
        <a href="#">G</a>
        <a href="#">f</a>
        <a href="#">◎</a>
        <a href="#">in</a>
      </div>

      {/* MENSAJES */}
      <h2>Hello, Welcome!</h2>

      <p>Don't have an account?</p>

      <button type="button">Register</button>

      <h2>Welcome Back!</h2>
    </div>
  );
}

export default LoginPage;