import { placeholders, categoriasPorIdioma } from "./data.js";

// Variables globales
const consultaInput = document.getElementById("consulta");
const languageSelect = document.querySelector(".language-select");
const loaderContainer = document.getElementById("loader-container");
const searchForm = document.getElementById("search-form");

// Event listeners
languageSelect.addEventListener("change", actualizarPlaceholder);
searchForm.addEventListener("submit", handleSubmit);

function actualizarPlaceholder() {
  const idioma = languageSelect.value;
  consultaInput.placeholder = placeholders[idioma] || placeholders["es"];
}

async function handleSubmit(e) {
  e.preventDefault();
  const consulta = consultaInput.value.trim();
  const idioma = languageSelect.value;

  if (!consulta) {
    alert("Por favor ingresa una consulta");
    return;
  }

  loaderContainer.classList.add("active");

  try {
    const response = await fetch("/buscar", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ consulta, idioma }),
    });

    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`);
    }

    const data = await response.json();
    renderResults(data, idioma);
  } catch (error) {
    console.error("Error en la búsqueda:", error);
    mostrarError();
  } finally {
    loaderContainer.classList.remove("active");
  }
}

function renderResults(data, idioma) {
  const contenedor = document.getElementById("resultados");
  contenedor.innerHTML = "";
  const fragment = document.createDocumentFragment();
  let hayResultados = false;

  const categorias = categoriasPorIdioma[idioma] || categoriasPorIdioma["es"];

  // Renderizar Ontología
  hayResultados =
    renderizarOntologia(data, categorias, fragment) || hayResultados;

  // Renderizar DBpedia
  hayResultados =
    renderizarDBpedia(data, categorias, fragment) || hayResultados;

  if (!hayResultados) {
    const mensaje = document.createElement("p");
    mensaje.textContent = categorias.no_resultados;
    fragment.appendChild(mensaje);
  }

  contenedor.appendChild(fragment);
  mostrarModal();
}

function renderizarOntologia(data, categorias, fragment) {
  let hayResultados = false;

  Object.keys(categorias).forEach((tipo) => {
    if (tipo !== "dbpedia" && tipo !== "no_resultados" && data[tipo]) {
      const valor = data[tipo];
      const nombre = categorias[tipo];

      if (tieneContenido(valor)) {
        hayResultados = true;
        fragment.appendChild(createSection(nombre, valor));
      }
    }
  });

  return hayResultados;
}

function renderizarDBpedia(data, categorias, fragment) {
  if (!data.descripcion_dbpedia) return false;

  const section = document.createElement("div");
  section.classList.add("dbpedia-section");

  // Título
  const titulo = document.createElement("h3");
  titulo.textContent = data.nombre || categorias.dbpedia;
  section.appendChild(titulo);

  // Descripción
  if (data.descripcion_dbpedia) {
    const p = document.createElement("p");
    p.textContent = data.descripcion_dbpedia;
    section.appendChild(p);
  }

  // País
  if (data.pais) {
    const paisTitulo = document.createElement("h4");
    paisTitulo.textContent = "Pais:";
    section.appendChild(paisTitulo);

    const paisLink = document.createElement("a");
    paisLink.href = data.pais;
    paisLink.textContent = data.pais;
    paisLink.target = "_blank";
    section.appendChild(paisLink);
  }

  // Ingredientes
  if (data.ingredientes && Array.isArray(data.ingredientes)) {
    const ingTitulo = document.createElement("h4");
    ingTitulo.textContent = "Ingredientes:";
    section.appendChild(ingTitulo);

    const ul = document.createElement("ul");
    data.ingredientes.forEach((ing) => {
      const li = document.createElement("li");
      li.textContent = ing;
      ul.appendChild(li);
    });
    section.appendChild(ul);
  }

  fragment.appendChild(section);
  return true;
}

function createSection(title, items) {
  const section = document.createElement("div");
  const titulo = document.createElement("h3");
  titulo.textContent = title;
  section.appendChild(titulo);

  const ul = document.createElement("ul");

  if (Array.isArray(items)) {
    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      ul.appendChild(li);
    });
  } else if (typeof items === "object") {
    for (const key in items) {
      const li = document.createElement("li");
      const propiedad = items[key];

      if (Array.isArray(propiedad)) {
        li.textContent = `${key}: ${propiedad.join(", ")}`;
      } else if (typeof propiedad === "object" && propiedad !== null) {
        li.textContent = `${key}:`;
        const innerUl = document.createElement("ul");
        Object.entries(propiedad).forEach(([innerKey, value]) => {
          const innerLi = document.createElement("li");
          innerLi.textContent = `${innerKey}: ${
            Array.isArray(value) ? value.join(", ") : value
          }`;
          innerUl.appendChild(innerLi);
        });
        li.appendChild(innerUl);
      } else {
        li.textContent = `${key}: ${propiedad}`;
      }
      ul.appendChild(li);
    }
  }

  section.appendChild(ul);
  return section;
}

function tieneContenido(valor) {
  return (
    valor &&
    (Array.isArray(valor) ? valor.length > 0 : Object.keys(valor).length > 0)
  );
}

function mostrarModal() {
  document.getElementById("result-modal").classList.add("show");
}

function mostrarError() {
  const contenedor = document.getElementById("resultados");
  contenedor.innerHTML = "";

  const errorDiv = document.createElement("div");
  errorDiv.className = "error-message";
  errorDiv.textContent =
    "Ha ocurrido un error en la búsqueda. Por favor, inténtalo de nuevo.";
  contenedor.appendChild(errorDiv);

  mostrarModal();
}
