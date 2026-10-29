import { NavLink } from 'react-router-dom';

export function ProyectosPage() {
  return (
    <div className="dashboard">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="logo">
          <div className="logo-icon">
            <span>⌂</span>
          </div>

          <div className="logo-text">
            <strong>CONSTRUINDUSTRIA</strong>
            <span>H.R.</span>
          </div>
        </div>

        <div className="welcome">
          <small>Bienvenido</small>
          <strong>Juan Rodríguez</strong>
          <small>Jefe</small>
        </div>

        <nav className="sidebar-menu">

          <NavLink to="/dashboard" className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">▦</span>
            <span>Dashboard</span>
          </NavLink>

          <NavLink to="/proyectos" end className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">▣</span>
            <span>Proyectos</span>
          </NavLink>

          <NavLink to="/clientes" className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">♙</span>
            <span>Clientes</span>
          </NavLink>

          <NavLink to="/precios" className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">$</span>
            <span>Precios</span>
          </NavLink>

          <NavLink to="/presupuestos" className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">▤</span>
            <span>Nuevo Presupuesto</span>
          </NavLink>

          <NavLink to="/reportes" className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">▥</span>
            <span>Reportes</span>
          </NavLink>

          <NavLink to="/historial" className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}>
            <span className="menu-icon">◴</span>
            <span>Historial</span>
          </NavLink>

        </nav>

        <div className="logout">
          <a href="#">
            <span className="logout-icon">↪</span>
            <span>Cerrar sesión</span>
          </a>
        </div>

      </aside>


      {/* MAIN */}
      <main className="main-content">

        {/* TOP BAR */}
        <header className="topbar">
          <h1>Proyectos</h1>

          <div className="online-status">
            <span className="wifi-icon">⌁</span>
            <span>En línea</span>
          </div>
        </header>


        {/* CONTENT */}
        <section className="content">

          {/* HEADING */}
          <div className="page-heading page-heading--actions">
            <div>
              <h2>GESTIÓN DE PROYECTOS</h2>
              <p>2 proyectos encontrados</p>
            </div>

            <a href="#" className="new-project-button">
              <span>+</span>
              <span>Nuevo Proyecto</span>
            </a>
          </div>


          {/* FILTERS */}
          <div className="filters-card">

            <label className="search-field">
              <span className="sr-only">Buscar por nombre o cliente</span>
              <span className="search-icon" aria-hidden="true">⌕</span>
              <input type="text" placeholder="Buscar por nombre o cliente..." />
            </label>

            <label className="filter-field">
              <span className="sr-only">Filtrar por estado</span>
              <span className="filter-icon" aria-hidden="true">⏷</span>
              <select defaultValue="todos">
                <option value="todos">Todos los estados</option>
                <option value="activo">Activo</option>
                <option value="por-confirmar">Por Confirmar</option>
                <option value="aprobado">Aprobado</option>
              </select>
            </label>

          </div>


          {/* PROJECT CARDS */}
          <div className="project-cards">

            {/* PROJECT 1 */}
            <article className="project-card">

              <div className="project-card__body">

                <span className="status active-status">
                  ↗ &nbsp;Activo
                </span>

                <h3>Casa de 2 pisos - Los Olivos</h3>

                <p className="client">Cliente: Carlos Mendoza</p>

                <dl className="project-card__details">
                  <div>
                    <dt>Área:</dt>
                    <dd>120m²</dd>
                  </div>
                  <div>
                    <dt>Altura:</dt>
                    <dd>6m</dd>
                  </div>
                  <div>
                    <dt>Tipo:</dt>
                    <dd>Vivienda unifamiliar</dd>
                  </div>
                  <div>
                    <dt>Presupuestos:</dt>
                    <dd>0</dd>
                  </div>
                </dl>

              </div>

              <footer className="project-card__footer">
                Actualizado: 9/4/2026
              </footer>

            </article>


            {/* PROJECT 2 */}
            <article className="project-card">

              <div className="project-card__body">

                <span className="status pending-status">
                  ⓘ &nbsp;Por Confirmar
                </span>

                <h3>Ampliación - San Juan</h3>

                <p className="client">Cliente: Ana Torres</p>

                <dl className="project-card__details">
                  <div>
                    <dt>Área:</dt>
                    <dd>45m²</dd>
                  </div>
                  <div>
                    <dt>Altura:</dt>
                    <dd>3m</dd>
                  </div>
                  <div>
                    <dt>Tipo:</dt>
                    <dd>Ampliación</dd>
                  </div>
                  <div>
                    <dt>Presupuestos:</dt>
                    <dd>0</dd>
                  </div>
                </dl>

              </div>

              <footer className="project-card__footer">
                Actualizado: 7/4/2026
              </footer>

            </article>

          </div>

        </section>

      </main>

    </div>
  );
}

export default ProyectosPage;
