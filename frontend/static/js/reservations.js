/* ============================================================
   KOI · Formulario de reservas
   ============================================================ */
(function () {
    'use strict';

    const form = document.getElementById('reservationForm');
    if (!form) return;

    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const submitBtn = document.getElementById('submitBtn');
    const formMessage = document.getElementById('formMessage');

    // ---- Fecha mínima = hoy ----
    const hoy = new Date();
    const hoyStr = hoy.toISOString().split('T')[0];
    dateInput.min = hoyStr;
    dateInput.value = hoyStr;

    // ---- Generar franjas horarias (12:00 – 15:30 y 20:00 – 22:30 cada 30 min) ----
    (function generarHoras() {
        timeSelect.innerHTML = '<option value="">Selecciona una hora</option>';

        // Turno de Comida: 12:00 a 15:30
        for (let h = 12; h <= 15; h++) {
            ['00', '30'].forEach(function (m) {
                const valor = String(h).padStart(2, '0') + ':' + m;
                const opt = document.createElement('option');
                opt.value = valor;
                opt.textContent = valor;
                timeSelect.appendChild(opt);
            });
        }

        // Turno de Cena: 20:00 a 22:30
        for (let h = 20; h <= 22; h++) {
            ['00', '30'].forEach(function (m) {
                const valor = String(h).padStart(2, '0') + ':' + m;
                const opt = document.createElement('option');
                opt.value = valor;
                opt.textContent = valor;
                timeSelect.appendChild(opt);
            });
        }
    })();

    // ---- Función para actualizar las horas desde el servidor ----
    async function actualizarHorasDisponibles() {
        const fecha = dateInput.value;
        const comensales = campoPorNombre('guests').value;

        // 1. GUARDAR LA HORA ELEGIDA ACTUALMENTE
        const horaPrevia = timeSelect.value;

        if (!fecha || !comensales) return;

        // Limpiamos y ponemos un estado de carga temporal
        timeSelect.innerHTML = '<option value="">Cargando horarios...</option>';

        try {
            const res = await fetch(`/api/reservations/availability?date=${fecha}&guests=${comensales}`);
            if (!res.ok) throw new Error();

            const mapaHoras = await res.json();

            timeSelect.innerHTML = '<option value="">Selecciona una hora</option>';

            // Estructura de turnos para mantener el orden visual
            const turnos = [
                { nombre: 'Comidas', horas: ['12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30'] },
                { nombre: 'Cenas', horas: ['20:00', '20:30', '21:00', '21:30', '22:00', '22:30'] }
            ];

            if (mapaHoras.error_cierre) {
                timeSelect.innerHTML = '<option value="">Restaurante Cerrado</option>';
                return;
            }

            let horaSigueDisponible = false;

            turnos.forEach(turno => {
                turno.horas.forEach(hora => {
                    const opt = document.createElement('option');
                    opt.value = hora;

                    const disponible = mapaHoras[hora];
                    if (!disponible) {
                        opt.disabled = true;
                        opt.textContent = hora + ' (Completo)';
                        opt.style.color = '#888'; // Gris visual en navegadores compatibles
                    } else {
                        opt.textContent = hora;
                        // 2. SI LA HORA PREVIA SIGUE LIBRE, LA SELECCIONAMOS
                        if (hora === horaPrevia) {
                            opt.selected = true;
                            horaSigueDisponible = true;
                        }
                    }

                    timeSelect.appendChild(opt);
                });
            });

            // 3. SI LA HORA ANTERIOR YA NO ESTÁ DISPONIBLE, LIMPIAMOS LA SELECCIÓN
            if (!horaSigueDisponible && horaPrevia) {
                timeSelect.value = '';
            }

        } catch (err) {
            timeSelect.innerHTML = '<option value="">Error al cargar horas</option>';
        }
    }

    // ---- Eventos para disparar la comprobación ----
    // Cuando cambie la fecha o el número de comensales, recalculamos los huecos grises
    dateInput.addEventListener('change', actualizarHorasDisponibles);
    campoPorNombre('guests').addEventListener('change', actualizarHorasDisponibles);

    // Ejecución inicial al cargar la página con la fecha de hoy
    actualizarHorasDisponibles();

    // ---- Validadores ----
    const validadores = {
        customer_name: function (v) {
            if (!v.trim()) return 'El nombre es obligatorio.';
            if (v.trim().length < 2) return 'Introduce un nombre válido.';
            return '';
        },
        customer_phone: function (v) {
            if (!v.trim()) return 'El teléfono es obligatorio.';
            if (!/^[+]?[\d\s()-]{6,20}$/.test(v.trim())) return 'Introduce un teléfono válido.';
            return '';
        },
        customer_email: function (v) {
            if (!v.trim()) return 'El correo es obligatorio.';
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())) return 'Introduce un correo válido.';
            return '';
        },
        date: function (v) {
            if (!v) return 'Selecciona una fecha.';
            if (v < hoyStr) return 'La fecha no puede ser anterior a hoy.';

            // Forzamos la lectura en formato UTC para evitar desfases de zona horaria
            const fechaSeleccionada = new Date(v);
            if (fechaSeleccionada.getUTCDay() === 2) {
                return 'El restaurante permanece cerrado los martes por descanso. Perdone las molestias';
            }
            return '';
        },
        time: function (v) { return v ? '' : 'Selecciona una hora.'; },
        guests: function (v) { return v ? '' : 'Indica el número de comensales.'; }
    };

    function campoPorNombre(nombre) { return form.querySelector('[name="' + nombre + '"]'); }
    function errorSpan(id) { return form.querySelector('.form-error[data-for="' + id + '"]'); }

    function validarCampo(nombre) {
        const validador = validadores[nombre];
        if (!validador) return true;
        const input = campoPorNombre(nombre);
        const mensaje = validador(input.value);
        const span = errorSpan(input.id);
        if (mensaje) {
            input.classList.add('is-invalid');
            if (span) span.textContent = mensaje;
            return false;
        }
        input.classList.remove('is-invalid');
        if (span) span.textContent = '';
        return true;
    }

    // Validación en tiempo real
    ['customer_name', 'customer_phone', 'customer_email', 'date', 'time', 'guests'].forEach(function (nombre) {
        const input = campoPorNombre(nombre);
        if (!input) return;
        input.addEventListener('blur', function () { validarCampo(nombre); });
        input.addEventListener('input', function () {
            if (input.classList.contains('is-invalid')) validarCampo(nombre);
        });
    });

    function mostrarMensaje(texto, tipo) {
        formMessage.hidden = false;
        formMessage.textContent = texto;
        formMessage.className = 'form-message form-message--' + tipo;
        formMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // ---- Envío ----
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        formMessage.hidden = true;

        const nombres = ['customer_name', 'customer_phone', 'customer_email', 'date', 'time', 'guests'];
        const todosValidos = nombres.map(validarCampo).every(Boolean);
        if (!todosValidos) {
            mostrarMensaje('Por favor, rellena todos los campos obligatorios', 'error');
            return;
        }

        const datos = {
            customer_name: campoPorNombre('customer_name').value.trim(),
            customer_phone: campoPorNombre('customer_phone').value.trim(),
            customer_email: campoPorNombre('customer_email').value.trim(),
            date: campoPorNombre('date').value,
            time: campoPorNombre('time').value,
            guests: parseInt(campoPorNombre('guests').value, 10),
            special_requests: (campoPorNombre('special_requests').value || '').trim() || null
        };

        submitBtn.disabled = true;
        submitBtn.textContent = 'Enviando…';

        try {
            const res = await fetch('/api/reservations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            });

            if (res.ok) {
                const reserva = await res.json();

                const partesFecha = datos.date.split('-');
                const fechaFormateada = partesFecha[2] + '/' + partesFecha[1] + '/' + partesFecha[0];

                mostrarMensaje(
                    '¡Gracias, ' + datos.customer_name + '! Tu reserva para ' + datos.guests +
                    ' personas el ' + fechaFormateada + ' a las ' + datos.time +
                    ' ha sido confirmada automáticamente. ¡Te esperamos en Koi!',
                    'success'
                );
                form.reset();
                dateInput.value = hoyStr;
            } else {
                let detalle = 'No se ha podido completar la reserva. Inténtalo de nuevo.';
                try {
                    const err = await res.json();
                    if (err.detail) {
                        detalle = typeof err.detail === 'string' ? err.detail : detalle;
                    }
                } catch (_) { /* respuesta sin JSON */ }
                mostrarMensaje(detalle, 'error');
            }
        } catch (err) {
            mostrarMensaje('Error de conexión. Comprueba tu red e inténtalo de nuevo.', 'error');
            console.error('Error al reservar:', err);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Confirmar reserva';
        }
    });
})();