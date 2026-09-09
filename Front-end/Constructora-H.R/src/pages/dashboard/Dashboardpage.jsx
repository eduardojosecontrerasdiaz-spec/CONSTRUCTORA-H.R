import {useState} from 'react';

export default function Dashboard() {
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
          Bienvenido
        </div>

        <nav className="sidebar-menu">

          <a href="#" className="menu-item active">
            <span className="menu-icon">▦</span>
            <span>Dashboard</span>
          </a>

          <a href="#" className="menu-item">
            <span className="menu-icon">▣</span>
            <span>Proyectos</span>
          </a>

          <a href="#" className="menu-item">
            <span className="menu-icon">♙</span>
            <span>Clientes</span>
          </a>

          <a href="#" className="menu-item">
            <span className="menu-icon">$</span>
            <span>Precios</span>
          </a>

          <a href="#" className="menu-item">
            <span className="menu-icon">▤</span>
            <span>Nuevo Presupuesto</span>
          </a>

          <a href="#" className="menu-item">
            <span className="menu-icon">◴</span>
            <span>Historial</span>
          </a>

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
          <h1>Dashboard</h1>

          <div className="online-status">
            <span className="wifi-icon">⌁</span>
            <span>En línea</span>
          </div>
        </header>


        {/* CONTENT */}
        <section className="content">

          {/* WELCOME */}
          <div className="page-heading">
            <h2>BIENVENIDO,</h2>
            <p>
              Aquí tienes un resumen de tus proyectos y actividades
            </p>
          </div>


          {/* STATISTICS */}
          <div className="statistics">

            <div className="stat-card">
              <div className="stat-icon green">
                ↗
              </div>

              <div className="stat-number">
                1
              </div>

              <div className="stat-label">
                Activos
              </div>
            </div>


            <div className="stat-card">
              <div className="stat-icon yellow">
                ◷
              </div>

              <div className="stat-number">
                1
              </div>

              <div className="stat-label">
                Por Confirmar
              </div>
            </div>


            <div className="stat-card">
              <div className="stat-icon green">
                ✓
              </div>

              <div className="stat-number">
                0
              </div>

              <div className="stat-label">
                Aprobados
              </div>
            </div>


            <div className="stat-card">
              <div className="stat-icon gray">
                ♧
              </div>

              <div className="stat-number">
                3
              </div>

              <div className="stat-label">
                Clientes
              </div>
            </div>

          </div>


          {/* QUICK ACCESS */}
          <section className="quick-section">

            <h2>ACCESOS RÁPIDOS</h2>

            <div className="quick-access">

              <a href="#" className="quick-card">

                <div className="quick-icon orange">
                  ▤
                </div>

                <span>
                  Crear Presupuesto
                </span>

              </a>


              <a href="#" className="quick-card">

                <div className="quick-icon orange">
                  $
                </div>

                <span>
                  Consultar Precios
                </span>

              </a>


              <a href="#" className="quick-card">

                <div className="quick-icon black">
                  ▣
                </div>

                <span>
                  Ver Proyectos
                </span>

              </a>


              <a href="#" className="quick-card">

                <div className="quick-icon gray-dark">
                  ♧
                </div>

                <span>
                  Clientes
                </span>

              </a>

            </div>

          </section>


          {/* RECENT PROJECTS */}
          <section className="projects-section">

            <div className="section-header">
              <h2>PROYECTOS RECIENTES</h2>

              <a href="#" className="view-all">
                Ver todos
                <span>↻</span>
              </a>
            </div>


            <div className="projects-list">

              {/* PROJECT 1 */}
              <article className="project-item">

                <div className="project-info">

                  <h3>
                    Casa de 2 pisos - Los Olivos
                  </h3>

                  <p className="client">
                    Cliente: Carlos Mendoza
                  </p>

                  <div className="project-details">
                    <span>Área: 120m²</span>
                    <span>Altura: 6m</span>
                    <span>Tipo: Vivienda unifamiliar</span>
                  </div>

                </div>


                <div className="project-status">

                  <span className="status active-status">
                    ↗ &nbsp;Activo
                  </span>

                  <div className="project-date">
                    <span>9/4/2026</span>
                    <small>7:00:00 p.m.</small>
                  </div>

                </div>

              </article>


              {/* PROJECT 2 */}
              <article className="project-item">

                <div className="project-info">

                  <h3>
                    Ampliación - San Juan
                  </h3>

                  <p className="client">
                    Cliente: Ana Torres
                  </p>

                  <div className="project-details">
                    <span>Área: 45m²</span>
                    <span>Altura: 3m</span>
                    <span>Tipo: Ampliación</span>
                  </div>

                </div>


                <div className="project-status">

                  <span className="status pending-status">
                    ⓘ &nbsp;Por Confirmar
                  </span>

                  <div className="project-date">
                    <span>7/4/2026</span>
                    <small>7:00:00 p.m.</small>
                  </div>

                </div>

              </article>

            </div>

          </section>

        </section>

      </main>

    </div>
  );
}