import { placeholders, categoriasPorIdioma } from "./data.js";

const consultaInput = document.getElementById("consulta");
const languageSelect = document.querySelector(".language-select");
const loaderContainer = document.getElementById("loader-container");
const searchForm = document.getElementById("search-form");

languageSelect.addEventListener("change", actualizarPlaceholder);
searchForm.addEventListener("submit", handleSubmit);

function actualizarPlaceholder() {
  const idioma = languageSelect.value;
  consultaInput.placeholder = placeholders[idioma] || placeholders["es"];
}

async function handleSubmit(e) {
  e.preventDefault();
  const consulta = consultaInput.value;
  const idioma = languageSelect.value;

  // Mostrar el loader
  loaderContainer.classList.add("active");

  try {
    const response = await fetch("/buscar", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ consulta, idioma }),
    });
    const data = await response.json();
    renderResults(data);
  } catch (error) {
    console.error("Error en la búsqueda:", error);
    loaderContainer.classList.remove("active");
  } finally {
    loaderContainer.classList.remove("active");
  }
}

function renderResults(data) {
  const contenedor = document.getElementById("resultados");
  contenedor.innerHTML = "";
  const fragment = document.createDocumentFragment();
  let hayResultados = false;

  const idioma = languageSelect.value;
  const categorias = categoriasPorIdioma[idioma] || categoriasPorIdioma["es"];

  // Renderizar Ontología
  Object.keys(categorias).forEach((tipo) => {
    if (tipo !== "dbpedia" && tipo !== "no_resultados" && data[tipo]) {
      const valor = data[tipo];
      const nombre = categorias[tipo];

      if (
        valor &&
        (Array.isArray(valor)
          ? valor.length > 0
          : Object.keys(valor).length > 0)
      ) {
        hayResultados = true;
        fragment.appendChild(createSection(nombre, valor));
      }
    }
  });

  // Renderizar DBpedia
  if (data.descripcion_dbpedia) {
    const dbpediaData = data.descripcion_dbpedia;
    if (Array.isArray(dbpediaData) && dbpediaData.length > 0) {
      fragment.appendChild(createSection(categorias.dbpedia, dbpediaData));
      hayResultados = true;
    } else if (typeof dbpediaData === "string" && dbpediaData !== "") {
      const section = document.createElement("div");
      const titulo = document.createElement("h3");
      titulo.textContent = categorias.dbpedia;
      section.appendChild(titulo);
      const p = document.createElement("p");
      p.textContent = dbpediaData;
      section.appendChild(p);
      fragment.appendChild(section);
      hayResultados = true;
    }
  }
  if (!hayResultados) {
    const mensaje = document.createElement("p");
    mensaje.textContent = categorias.no_resultados;
    fragment.appendChild(mensaje);
  }
  contenedor.appendChild(fragment);
  mostrarModal();
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
function mostrarModal() {
  document.getElementById("result-modal").classList.add("show");
}
