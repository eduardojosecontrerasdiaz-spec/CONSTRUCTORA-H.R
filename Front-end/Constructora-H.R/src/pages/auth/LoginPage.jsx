import { useState } from 'react';

export function LoginPage() {
  const [isRegistering, setIsRegistering] = useState(false);

  const switchMode = (event) => {
    event.preventDefault();
    setIsRegistering((currentMode) => !currentMode);
  };

  return (
    <main className={`auth-page ${isRegistering ? 'auth-page--register' : ''}`}>
      <section className="auth-card" aria-label="Authentication">
        <div className="auth-panel">
          <div className="auth-panel__content">
            <h1>{isRegistering ? 'Welcome Back!' : 'Hello, Welcome!'}</h1>
            <p>{isRegistering ? 'Already have an account?' : "Don't have an account?"}</p>
            <button className="auth-button auth-button--outline" type="button" onClick={switchMode}>
              {isRegistering ? 'Login' : 'Register'}
            </button>
          </div>
        </div>

        <div className="auth-form-area">
          {isRegistering ? (
            <form className="auth-form">
              <h2>Registration</h2>
              <InputField type="text" placeholder="Username" icon="👤" />
              <InputField type="email" placeholder="Email" icon="✉" />
              <InputField type="password" placeholder="Password" icon="🔒" />
              <button className="auth-button" type="submit">Register</button>
              <p className="social-label">or register with social platforms</p>
              <SocialLinks />
            </form>
          ) : (
            <form className="auth-form">
              <h2>Login</h2>
              <InputField type="text" placeholder="Username" icon="👤" />
              <InputField type="password" placeholder="Password" icon="🔒" />
              <a className="forgot-link" href="#forgot-password">Forgot Password?</a>
              <button className="auth-button" type="submit">Login</button>
              <p className="social-label">or login with social platforms</p>
              <SocialLinks />
            </form>
          )}
        </div>
      </section>
    </main>
  );
}

function InputField({ type, placeholder, icon }) {
  return (
    <label className="input-group">
      <span className="sr-only">{placeholder}</span>
      <input type={type} placeholder={placeholder} />
      <span aria-hidden="true">{icon}</span>
    </label>
  );
}

function SocialLinks() {
  return (
    <div className="social-links" aria-label="Social platforms">
      <a href="#google" aria-label="Google">G</a>
      <a href="#facebook" aria-label="Facebook">f</a>
      <a href="#github" aria-label="GitHub">◉</a>
      <a href="#linkedin" aria-label="LinkedIn">in</a>
    </div>
  );
}

export default LoginPage;