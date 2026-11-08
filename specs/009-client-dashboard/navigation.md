# Ajuste SDD — Acceso independiente y móvil

Ampliación solicitada durante la revisión de SPEC-009, todavía sin commit.

## Criterios
- La página comercial no muestra el formulario de login ni los dashboards.
- Cabecera: botón «Acceso clientes» / «Client access», que abre una pantalla dedicada. Con
  sesión válida: «Mi panel» / «My dashboard», acceso directo al panel del rol.
- Conservar enlaces #access y #client-hours anteriores. Nuevos accesos #login y
  #panel, sin añadir dependencias ni requerir rutas de servidor especiales.
- En móvil el acceso y el idioma permanecen visibles; menú desplegable con estado
  accesible, Escape y enlaces táctiles de al menos 44 px. Mantener navegación de escritorio.
- Login, logout, recarga, Atrás, ES/EN y navegación entre web/panel funcionan.
- No confiar en la navegación para autorizar: permisos siguen en backend.
- Revisar 320, 390, 768 y 1440 px y recorrido de ambos roles en API temporal.

## Plan
App controla la vista mediante hash y sincroniza el indicador de sesión con
AccessPanel y /auth/me. AccessPanel se monta solo en la vista privada y conserva
sus componentes existentes. Los anclajes internos del cliente mantienen el panel.
Las entradas heredadas se normalizan después de verificar la sesión.

Ajuste comercial aprobado: acceso con borde discreto, texto de cuenta asignada al negocio y enlace «Solicitar asesoría» / «Request a consultation» a #contact para visitantes sin cuenta. El acceso de Super Admin se conserva.

Cabecera sticky aprobada: permanecer visible al desplazar, medir su altura real para compensar anclajes y permitir desplazamiento del menú móvil si ocupa la altura disponible. Verificar títulos visibles tras navegación y cabecera anclada en móvil/escritorio.
