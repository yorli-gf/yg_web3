import './App.css';
import React, { useState, useEffect } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8089";

function App() {
  const [numeros, setNumeros] = useState("");
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Estado para filtros y ordenamiento
  const [filtroOperacion, setFiltroOperacion] = useState("");
  const [filtroFecha, setFiltroFecha] = useState("");
  const [ordenarPor, setOrdenarPor] = useState("");
  const [orden, setOrden] = useState("desc");

  const operar = async (tipo) => {
    try {
      setLoading(true);
      const nums = numeros
        .split(",")
        .map(n => parseFloat(n.trim()))
        .filter(n => !isNaN(n));

      if (nums.length === 0) {
        setResultado("❌ Por favor ingresa números válidos");
        return;
      }

      const res = await fetch(`${API_URL}/calculadora/${tipo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ numeros: nums })
      });

      const data = await res.json();

      if (res.ok) {
        setResultado(`${data.operacion}: ${data.resultado}`);
        obtenerHistorial();
      } else {
        setResultado(`❌ Error: ${data.detail?.error || data.detail}`);
      }
    } catch (err) {
      console.error(err);
      setResultado("❌ Error de conexión con el backend");
    } finally {
      setLoading(false);
    }
  };

  const obtenerHistorial = async () => {
    try {
      // Construir parámetros de consulta
      const params = new URLSearchParams();
      if (filtroOperacion) params.append('operacion', filtroOperacion);
      if (filtroFecha) params.append('fecha', filtroFecha);
      if (ordenarPor) params.append('ordenar_por', ordenarPor);
      if (orden) params.append('orden', orden);

      const url = `${API_URL}/calculadora/historial?${params.toString()}`;
      const res = await fetch(url);
      const data = await res.json();
      setHistorial(data.historial || []);
    } catch (err) {
      console.error("Error al cargar historial:", err);
    }
  };

  // Limpiar todos los filtros
  const limpiarFiltros = () => {
    setFiltroOperacion("");
    setFiltroFecha("");
    setOrdenarPor("");
    setOrden("desc");
  };

  useEffect(() => {
    obtenerHistorial();
  }, [filtroOperacion, filtroFecha, ordenarPor, orden]);

  useEffect(() => {
    obtenerHistorial();
  }, []);

  const colors = {
    primary: '#8B5FBF',
    primaryDark: '#6B46C1',
    primaryLight: '#9F7AEA',
    secondary: '#D6BCFA',
    background: '#FAF5FF',
    card: '#FFFFFF',
    text: '#2D3748',
    textLight: '#718096',
    border: '#E9D8FD',
    success: '#48BB78',
    error: '#F56565'
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: `linear-gradient(135deg, ${colors.background} 0%, #EDF2F7 100%)`,
      padding: 20,
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    }}>
      <div style={{
        maxWidth: 800,
        margin: '0 auto',
        background: colors.card,
        borderRadius: 20,
        boxShadow: '0 10px 30px rgba(139, 95, 191, 0.1)',
        overflow: 'hidden'
      }}>
        
        {/* Header */}
        <div style={{
          background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.primaryDark} 100%)`,
          color: 'white',
          padding: '30px 20px',
          textAlign: 'center'
        }}>
          <h1 style={{ 
            margin: 0, 
            fontSize: '2.5rem',
            fontWeight: '700',
            textShadow: '2px 2px 4px rgba(0,0,0,0.2)'
          }}>
            🧮 Calculadora
          </h1>
          <p style={{ 
            margin: '10px 0 0 0',
            opacity: 0.9,
            fontSize: '1.1rem'
          }}>
            Realiza operaciones con múltiples números
          </p>
        </div>

        {/* Sección de operaciones */}
        <div style={{ padding: 30 }}>
          <div style={{
            background: colors.background,
            padding: 25,
            borderRadius: 15,
            border: `2px dashed ${colors.border}`,
            marginBottom: 25
          }}>
            <input
              type="text"
              value={numeros}
              onChange={(e) => setNumeros(e.target.value)}
              placeholder="🔢 Ingresa números separados por coma (ej: 10, 5, 2, 8)"
              style={{
                width: '90%',
                padding: '15px 20px',
                marginBottom: 20,
                borderRadius: 12,
                border: `2px solid ${colors.border}`,
                fontSize: '16px',
                outline: 'none',
                transition: 'all 0.3s ease',
                background: colors.card
              }}
              onFocus={(e) => e.target.style.borderColor = colors.primary}
              onBlur={(e) => e.target.style.borderColor = colors.border}
            />

            <div style={{ 
              display: 'flex', 
              gap: 12, 
              flexWrap: 'wrap',
              justifyContent: 'center'
            }}>
              {['sum', 'sub', 'mul', 'div'].map((operacion) => (
                <button 
                  key={operacion}
                  onClick={() => operar(operacion)}
                  disabled={loading}
                  style={{
                    ...btnStyle,
                    background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.primaryLight} 100%)`,
                    opacity: loading ? 0.6 : 1,
                    transform: loading ? 'scale(0.98)' : 'scale(1)',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseOver={(e) => !loading && (e.target.style.transform = 'scale(1.05)')}
                  onMouseOut={(e) => !loading && (e.target.style.transform = 'scale(1)')}
                >
                  {loading ? '⏳' : getOperacionIcon(operacion)} {getOperacionTexto(operacion)}
                </button>
              ))}
            </div>

            {resultado && (
              <div style={{
                marginTop: 20,
                padding: 15,
                borderRadius: 12,
                background: resultado.includes('❌') ? '#FED7D7' : '#C6F6D5',
                border: `2px solid ${resultado.includes('❌') ? colors.error : colors.success}`,
                color: resultado.includes('❌') ? colors.error : '#22543D',
                fontSize: '18px',
                fontWeight: '600'
              }}>
                {resultado}
              </div>
            )}
          </div>

          {/* Sección de filtros */}
          <div style={{
            background: colors.background,
            padding: 25,
            borderRadius: 15,
            marginBottom: 25,
            border: `1px solid ${colors.border}`
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 20
            }}>
              <h3 style={{ 
                margin: 0, 
                color: colors.primaryDark,
                fontSize: '1.4rem'
              }}>
                🎛️ Filtros y Ordenamiento
              </h3>
              <button 
                onClick={limpiarFiltros}
                style={{
                  ...btnStyle,
                  background: colors.textLight,
                  padding: '8px 16px',
                  fontSize: '14px'
                }}
              >
                🗑️ Limpiar
              </button>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr 1fr',
              gap: 15
            }}>
              <div>
                <label style={labelStyle}>📊 Operación</label>
                <select 
                  value={filtroOperacion} 
                  onChange={(e) => setFiltroOperacion(e.target.value)}
                  style={selectStyle}
                >
                  <option value="">Todas las operaciones</option>
                  <option value="suma">Suma</option>
                  <option value="resta">Resta</option>
                  <option value="multiplicación">Multiplicación</option>
                  <option value="división">División</option>
                </select>
              </div>

              <div>
                <label style={labelStyle}>📅 Fecha</label>
                <input
                  type="date"
                  value={filtroFecha}
                  onChange={(e) => setFiltroFecha(e.target.value)}
                  style={{
                    ...selectStyle, 
                    fontFamily: 'inherit'
                  }}
                />
              </div>

              <div>
                <label style={labelStyle}>🔀 Ordenar por</label>
                <select 
                  value={ordenarPor} 
                  onChange={(e) => setOrdenarPor(e.target.value)}
                  style={selectStyle}
                >
                  <option value="">Sin ordenar</option>
                  <option value="date">Fecha</option>
                  <option value="resultado">Resultado</option>
                </select>
              </div>

              <div>
                <label style={labelStyle}>📈 Orden</label>
                <select 
                  value={orden} 
                  onChange={(e) => setOrden(e.target.value)}
                  style={selectStyle}
                >
                  <option value="desc">Descendente ↓</option>
                  <option value="asc">Ascendente ↑</option>
                </select>
              </div>
            </div>
          </div>

          {/* Historial */}
          <div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 20
            }}>
              <h3 style={{ 
                margin: 0, 
                color: colors.primaryDark,
                fontSize: '1.4rem'
              }}>
                📜 Historial ({historial.length} operaciones)
              </h3>
              <button 
                onClick={obtenerHistorial}
                style={{
                  ...btnStyle,
                  background: `linear-gradient(135deg, ${colors.primaryLight} 0%, ${colors.primary} 100%)`,
                  padding: '8px 16px'
                }}
              >
                🔄 Actualizar
              </button>
            </div>

            {historial.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '40px 20px',
                color: colors.textLight,
                background: colors.background,
                borderRadius: 15,
                border: `2px dashed ${colors.border}`
              }}>
                <div style={{ fontSize: '3rem', marginBottom: 10 }}>📭</div>
                <h4 style={{ margin: '0 0 10px 0', color: colors.text }}>
                  {filtroOperacion || filtroFecha ? 'No hay operaciones con los filtros aplicados' : 'No hay operaciones en el historial'}
                </h4>
                <p>Realiza alguna operación para verla aquí</p>
              </div>
            ) : (
              <div style={{ 
                maxHeight: 500, 
                overflowY: 'auto',
                borderRadius: 15
              }}>
                {historial.map((op, i) => (
                  <div key={i} style={{
                    margin: '8px 0',
                    padding: '20px',
                    background: i % 2 === 0 ? colors.card : colors.background,
                    borderRadius: 12,
                    border: `1px solid ${colors.border}`,
                    transition: 'all 0.2s ease'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          color: getColorByOperation(op.operacion),
                          textTransform: 'capitalize',
                          fontWeight: '700',
                          fontSize: '1.1rem',
                          marginBottom: 8
                        }}>
                          {getOperacionIconByText(op.operacion)} {op.operacion}
                        </div>
                        <div style={{ marginBottom: 5, color: colors.text }}>
                          <strong>Números:</strong> 
                          <span style={{ 
                            background: colors.secondary, 
                            padding: '2px 8px', 
                            borderRadius: 6,
                            marginLeft: 8
                          }}>
                            [{op.numeros.join(", ")}]
                          </span>
                        </div>
                        <div style={{ marginBottom: 5, color: colors.text }}>
                          <strong>Resultado:</strong> 
                          <span style={{ 
                            fontWeight: '800', 
                            color: colors.primaryDark,
                            fontSize: '1.1rem',
                            marginLeft: 8
                          }}>
                            {op.resultado}
                          </span>
                        </div>
                        <div style={{ fontSize: '14px', color: colors.textLight }}>
                          ⏰ {new Date(op.date).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const getOperacionIcon = (operacion) => {
  switch(operacion) {
    case 'sum': return '➕';
    case 'sub': return '➖';
    case 'mul': return '✖️';
    case 'div': return '➗';
    default: return '🔢';
  }
};

const getOperacionTexto = (operacion) => {
  switch(operacion) {
    case 'sum': return 'Sumar';
    case 'sub': return 'Restar';
    case 'mul': return 'Multiplicar';
    case 'div': return 'Dividir';
    default: return 'Operar';
  }
};

const getOperacionIconByText = (operacion) => {
  switch(operacion) {
    case 'suma': return '➕';
    case 'resta': return '➖';
    case 'multiplicación': return '✖️';
    case 'división': return '➗';
    default: return '🔢';
  }
};

const getColorByOperation = (operacion) => {
  const colors = {
    primary: '#8B5FBF',
    success: '#48BB78',
    warning: '#ED8936',
    info: '#4299E1'
  };
  
  switch(operacion) {
    case 'suma': return colors.success;
    case 'resta': return colors.warning;
    case 'multiplicación': return colors.info;
    case 'división': return colors.primary;
    default: return '#718096';
  }
};

const btnStyle = {
  padding: '12px 24px',
  border: 'none',
  borderRadius: 12,
  color: 'white',
  cursor: 'pointer',
  fontSize: '16px',
  fontWeight: '600',
  transition: 'all 0.3s ease',
  boxShadow: '0 4px 12px rgba(139, 95, 191, 0.3)'
};

const labelStyle = {
  display: 'block',
  marginBottom: 8,
  fontWeight: '600',
  color: '#2D3748',
  fontSize: '14px'
};

const selectStyle = {
  width: '100%',
  padding: '12px 16px',
  borderRadius: 10,
  border: '2px solid #E9D8FD',
  fontSize: '14px',
  outline: 'none',
  transition: 'all 0.3s ease',
  background: 'white',
  boxSizing: 'border-box'
};

const inputStyle = {
  ...selectStyle,
  fontFamily: 'inherit'
};

export default App;

