module servo_pwm_smooth #(
    parameter integer CLK_FREQ_HZ        = 50_000_000, 
    parameter integer PERIOD_MS          = 20,         
    parameter integer MIN_PULSE_US       = 600,        
    parameter integer MAX_PULSE_US       = 2400,
    parameter integer SMOOTH_DELAY_MS    = 8 // Milisegundos entre cada paso de movimiento (Mayor = Más lento/Suave)
)(
    input  wire clk,
    input  wire reset,
    input  wire [7:0] target_pos,   // Posición a la que QUEREMOS ir (0..255)
    output reg pwm_out
);

    // --- CÁLCULOS DE PWM ---
    localparam integer PERIOD_CYCLES = (CLK_FREQ_HZ / 1000) * PERIOD_MS; 
    localparam integer MIN_PULSE_CYCLES = (CLK_FREQ_HZ / 1_000_000) * MIN_PULSE_US; 
    localparam integer MAX_PULSE_CYCLES = (CLK_FREQ_HZ / 1_000_000) * MAX_PULSE_US; 

    // --- CÁLCULOS DE SUAVIZADO ---
    // Cuantos ciclos de reloj esperar antes de mover el servo un pasito más
    localparam integer STEP_DELAY_CYCLES = (CLK_FREQ_HZ / 1000) * SMOOTH_DELAY_MS;

    reg [31:0] pwm_counter = 0;
    reg [31:0] move_timer = 0;
    
    // "internal_pos" es donde está el servo REALMENTE ahora mismo.
    // Usamos un registro ampliado para precisión, pero aquí simple 8 bits basta.
    reg [7:0] current_pos = 0; 

    // Cálculo del ancho de pulso actual basado en la posición suavizada
    // pulse = MIN + current_pos * (MAX-MIN)/255
    wire [31:0] span = MAX_PULSE_CYCLES - MIN_PULSE_CYCLES;
    reg [31:0] active_pulse_width;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            pwm_counter <= 0;
            pwm_out <= 1'b0;
            move_timer <= 0;
            current_pos <= 127; // Arrancar en el centro para evitar saltos bruscos al inicio
            active_pulse_width <= MIN_PULSE_CYCLES + (span * 127 / 255);
        end else begin
            
            // --- 1. LÓGICA DE MOVIMIENTO SUAVE (RAMPA) ---
            move_timer <= move_timer + 1;
            
            if (move_timer >= STEP_DELAY_CYCLES) begin
                move_timer <= 0; // Reiniciar timer de paso
                
                // Si estamos lejos del objetivo, nos acercamos 1 paso
                if (current_pos < target_pos) begin
                    current_pos <= current_pos + 1;
                end 
                else if (current_pos > target_pos) begin
                    current_pos <= current_pos - 1;
                end
                // Si current_pos == target_pos, no hacemos nada (ya llegamos)
                
                // Actualizamos el ancho del pulso solo cuando cambia la posición
                active_pulse_width <= MIN_PULSE_CYCLES + (span * current_pos / 255);
            end


            // --- 2. GENERACIÓN PWM ESTÁNDAR ---
            if (pwm_counter >= PERIOD_CYCLES - 1)
                pwm_counter <= 0;
            else
                pwm_counter <= pwm_counter + 1;

            pwm_out <= (pwm_counter < active_pulse_width) ? 1'b1 : 1'b0;
        end
    end

endmodule