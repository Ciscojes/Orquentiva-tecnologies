export type Language = "es" | "en";
export type ServiceId = "agents" | "automation" | "growth" | "saas";
export type Service = {
  id: ServiceId; name: string; subtitle: string; description: string;
  example: string; problem: string; includes: string[]; benefits: string;
  steps: string[]; audience: string; scope: string;
};

export const services: Record<Language, Service[]> = {
  "es": [
    {
      "id": "agents",
      "name": "Agentes de Inteligencia Artificial",
      "subtitle": "Atención inteligente para tus clientes.",
      "description": "Diseñamos asistentes de IA para responder consultas, orientar a tus clientes y gestionar solicitudes de reserva mediante integraciones autorizadas.",
      "example": "Una barbería podría responder preguntas sobre servicios y canalizar solicitudes de citas, con apoyo de su equipo cuando sea necesario.",
      "problem": "Las consultas repetidas y los mensajes sin responder pueden consumir tiempo y dejar oportunidades sin atender.",
      "includes": [
        "Definición de preguntas frecuentes y fuentes de información aprobadas.",
        "Diseño de conversaciones y derivación al equipo humano.",
        "Integración con canales y sistemas de reservas acordados, con pruebas antes de activarlos."
      ],
      "benefits": "Puede facilitar respuestas consistentes y reducir la carga de consultas repetitivas. La calidad depende de la información disponible y de la supervisión.",
      "steps": [
        "Revisamos las consultas y los canales de atención.",
        "Definimos respuestas, permisos y casos que requieren una persona.",
        "Probamos un piloto y acordamos seguimiento y mejoras."
      ],
      "audience": "Barberías, centros de estética y empresas de servicios que reciben consultas frecuentes.",
      "scope": "El asistente se desarrolla para cada proyecto. Las reservas requieren conexión autorizada con el sistema del negocio y validación de disponibilidad."
    },
    {
      "id": "automation",
      "name": "Automatización de Negocios",
      "subtitle": "Menos tareas repetitivas, más tiempo para crecer.",
      "description": "Diseñamos flujos que conectan tus herramientas para simplificar confirmaciones, recordatorios, seguimiento comercial y tareas administrativas.",
      "example": "Una barbería podría enviar confirmaciones y recordatorios de citas desde su sistema de reservas, según los canales y permisos acordados.",
      "problem": "Copiar datos entre aplicaciones y enviar avisos manuales puede provocar retrasos, olvidos y trabajo duplicado.",
      "includes": [
        "Revisión y documentación de los procesos seleccionados.",
        "Diseño de conexiones entre herramientas, utilizando opciones como n8n según el proyecto.",
        "Reglas de ejecución, gestión de errores y pruebas con el equipo."
      ],
      "benefits": "Puede reducir trabajo manual y mejorar la continuidad de los procesos. El ahorro depende del volumen de tareas y de las integraciones disponibles.",
      "steps": [
        "Identificamos una tarea repetitiva y cómo se realiza hoy.",
        "Definimos reglas, permisos y herramientas compatibles.",
        "Probamos el flujo y acordamos su puesta en marcha y mantenimiento."
      ],
      "audience": "Negocios con reservas, equipos comerciales y empresas que repiten tareas entre varias aplicaciones.",
      "scope": "Las automatizaciones y n8n se implementarían dentro del proyecto contratado; no están operativos en esta web. Licencias y costes externos se detallan en la propuesta."
    },
    {
      "id": "growth",
      "name": "Crecimiento Empresarial (Growth Partner)",
      "subtitle": "Estrategias y tecnología para impulsar tu negocio.",
      "description": "Actuamos como socio tecnológico y estratégico para mejorar tus procesos comerciales, captar oportunidades y dar seguimiento a clientes interesados.",
      "example": "Una barbería podría identificar dónde se pierden consultas y mejorar su seguimiento para facilitar que se conviertan en reservas.",
      "problem": "Sin un proceso de seguimiento y medición, es difícil saber qué oportunidades avanzan y dónde mejorar la atención comercial.",
      "includes": [
        "Diagnóstico del recorrido desde la primera consulta hasta la contratación.",
        "Propuesta de mejoras en captación, registro de oportunidades y seguimiento.",
        "Definición de indicadores y revisiones de resultados con el equipo."
      ],
      "benefits": "Puede aportar visibilidad sobre el proceso comercial y ayudar a priorizar mejoras basadas en datos. No garantiza ventas ni un porcentaje de crecimiento.",
      "steps": [
        "Analizamos el proceso comercial y los datos disponibles.",
        "Acordamos objetivos, indicadores y acciones prioritarias.",
        "Medimos lo realizado y ajustamos las acciones con tu equipo."
      ],
      "audience": "Negocios de servicios y pequeñas empresas que quieren organizar su seguimiento comercial y tomar decisiones con datos.",
      "scope": "El alcance se acuerda según el diagnóstico. No se incluyen campañas publicitarias ni inversión en anuncios salvo que se definan expresamente en una propuesta."
    },
    {
      "id": "saas",
      "name": "Desarrollo de Software Empresarial",
      "subtitle": "Soluciones digitales diseñadas para tu empresa.",
      "description": "Desarrollamos aplicaciones, paneles de gestión, sistemas de reservas y herramientas SaaS: software al que tu equipo puede acceder por internet.",
      "example": "Una clínica podría administrar servicios y citas desde un sistema adaptado a su operación y a los permisos de su equipo.",
      "problem": "Las hojas de cálculo y las herramientas desconectadas pueden dificultar el acceso a información y la coordinación del equipo.",
      "includes": [
        "Definición de requisitos y diseño de pantallas con el negocio.",
        "Desarrollo por etapas de las funciones e integraciones acordadas.",
        "Pruebas, documentación y propuesta de despliegue y mantenimiento."
      ],
      "benefits": "Puede centralizar información y facilitar el trabajo del equipo. Los resultados dependen del alcance, la adopción y el mantenimiento de la solución.",
      "steps": [
        "Definimos usuarios, procesos y funciones prioritarias.",
        "Validamos el diseño y construimos una primera versión.",
        "Probamos con el equipo y planificamos despliegue y evolución."
      ],
      "audience": "Clínicas, negocios con citas y empresas que necesitan herramientas adaptadas o una plataforma para varias empresas.",
      "scope": "Cada solución se construye según requisitos acordados. Accesos, separación entre empresas, protección de datos y costes de operación se definen antes del despliegue."
    }
  ],
  "en": [
    {
      "id": "agents",
      "name": "Artificial Intelligence Agents",
      "subtitle": "Intelligent support for your customers.",
      "description": "We design AI assistants to answer questions, guide customers and handle booking requests through authorized integrations.",
      "example": "A barbershop could answer questions about its services and route appointment requests, with staff support when needed.",
      "problem": "Repeated questions and unanswered messages can take up staff time and leave potential customers waiting.",
      "includes": [
        "Define frequently asked questions and approved information sources.",
        "Design conversations and handoffs to your team.",
        "Integrate agreed channels and booking systems, testing before activation."
      ],
      "benefits": "Can support consistent answers and reduce repetitive inquiries for your staff. Quality depends on the available information and supervision.",
      "steps": [
        "Review customer questions and support channels.",
        "Define answers, permissions and cases that need a person.",
        "Test a pilot and agree on monitoring and improvements."
      ],
      "audience": "Barbershops, beauty salons and service businesses that receive frequent customer questions.",
      "scope": "Each assistant is developed for its project. Bookings require an authorized connection to the business system and availability checks."
    },
    {
      "id": "automation",
      "name": "Business Automation",
      "subtitle": "Fewer repetitive tasks, more time to grow.",
      "description": "We design workflows that connect your tools to simplify confirmations, reminders, sales follow-up and administrative tasks.",
      "example": "A barbershop could send appointment confirmations and reminders from its booking system using agreed channels and permissions.",
      "problem": "Copying data between applications and sending messages manually can lead to delays, missed tasks and duplicate work.",
      "includes": [
        "Review and document selected processes.",
        "Design connections between tools, using options such as n8n where appropriate.",
        "Define execution rules, error handling and tests with your team."
      ],
      "benefits": "Can reduce manual work and improve process continuity. Savings depend on task volume and available integrations.",
      "steps": [
        "Identify a repetitive task and how it works today.",
        "Define rules, permissions and compatible tools.",
        "Test the workflow and agree on launch and maintenance."
      ],
      "audience": "Appointment-based businesses, sales teams and companies repeating tasks across multiple applications.",
      "scope": "Automations and n8n would be implemented within the agreed project; they are not running on this website. External licenses and costs are detailed in the proposal."
    },
    {
      "id": "growth",
      "name": "Business Growth (Growth Partner)",
      "subtitle": "Strategy and technology to support your business.",
      "description": "We work as a technology and strategy partner to improve sales processes, capture opportunities and follow up with interested customers.",
      "example": "A barbershop could identify where inquiries are lost and improve follow-up to help customers move toward a booking.",
      "problem": "Without follow-up and measurement, it is difficult to see which opportunities progress and where the sales process needs attention.",
      "includes": [
        "Assess the journey from the first inquiry to a purchase or booking.",
        "Propose improvements to lead capture, opportunity tracking and follow-up.",
        "Define metrics and review results with your team."
      ],
      "benefits": "Can provide visibility into the sales process and help prioritize improvements based on data. It does not guarantee sales or a growth percentage.",
      "steps": [
        "Review your sales process and available data.",
        "Agree on objectives, metrics and priority actions.",
        "Measure the work and adjust actions with your team."
      ],
      "audience": "Service businesses and small companies seeking more organized sales follow-up and decisions informed by data.",
      "scope": "Scope is agreed after the assessment. Advertising campaigns and ad spend are not included unless explicitly defined in a proposal."
    },
    {
      "id": "saas",
      "name": "Business Software Development",
      "subtitle": "Digital solutions designed for your company.",
      "description": "We develop applications, management dashboards, booking systems and SaaS tools: software your team can access over the internet.",
      "example": "A clinic could manage services and appointments through a system tailored to its operations and staff permissions.",
      "problem": "Spreadsheets and disconnected tools can make information harder to access and teamwork harder to coordinate.",
      "includes": [
        "Define requirements and design screens with the business.",
        "Develop agreed features and integrations in stages.",
        "Provide tests, documentation and a deployment and maintenance proposal."
      ],
      "benefits": "Can centralize information and support teamwork. Results depend on scope, adoption and ongoing maintenance.",
      "steps": [
        "Define users, processes and priority features.",
        "Validate the design and build an initial version.",
        "Test with the team and plan deployment and future improvements."
      ],
      "audience": "Clinics, appointment-based businesses and companies needing custom tools or a platform serving multiple businesses.",
      "scope": "Each solution is built to agreed requirements. Access controls, separation between businesses, data protection and running costs are defined before deployment."
    }
  ]
};
