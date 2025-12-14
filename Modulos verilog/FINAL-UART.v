module uart_rx #(
    parameter CLK_FREQ = 50000000, // Frecuencia del reloj de la FPGA (50MHz)
    parameter BAUD_RATE = 9600     // Velocidad del HC-05
)(
    input wire clk,
    input wire rst_n,
    input wire rx_serial,          // Pin conectado al TX del HC-05
    output reg data_ready,         // Se pone en 1 durante un ciclo cuando llega un dato
    output reg [7:0] data_byte     // El byte recibido (ASCII)
);

    // Cálculo de cuantos ciclos de reloj dura un bit
    localparam CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;
    localparam HALF_BIT     = CLKS_PER_BIT / 2;

    // Estados de la FSM
    localparam IDLE         = 3'b000;
    localparam START_BIT    = 3'b001;
    localparam DATA_BITS    = 3'b010;
    localparam STOP_BIT     = 3'b011;
    localparam CLEANUP      = 3'b100;

    reg [2:0] state;
    reg [15:0] clk_count; // Contador para medir el tiempo de cada bit
    reg [2:0] bit_index;  // Para contar los bits del 0 al 7

    // Sincronización de señal (evitar metaestabilidad)
    reg rx_sync_1, rx_sync_2;
    wire rx_safe = rx_sync_2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync_1 <= 1'b1;
            rx_sync_2 <= 1'b1;
        end else begin
            rx_sync_1 <= rx_serial;
            rx_sync_2 <= rx_sync_1;
        end
    end

    // Máquina de estados UART
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            clk_count <= 0;
            bit_index <= 0;
            data_ready <= 0;
            data_byte <= 0;
        end else begin
            case (state)
                // 1. Esperar a que la línea baje a 0 (Start Bit)
                IDLE: begin
                    data_ready <= 0;
                    clk_count <= 0;
                    bit_index <= 0;
                    if (rx_safe == 1'b0) begin 
                        state <= START_BIT;
                    end
                end

                // 2. Verificar que sigue en 0 a la mitad del bit (Evitar ruido)
                START_BIT: begin
                    if (clk_count == HALF_BIT) begin
                        if (rx_safe == 1'b0) begin
                            clk_count <= 0;
                            state <= DATA_BITS;
                        end else begin
                            state <= IDLE; // Falsa alarma
                        end
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                // 3. Leer los 8 bits de datos
                DATA_BITS: begin
                    if (clk_count == CLKS_PER_BIT) begin
                        clk_count <= 0;
                        data_byte[bit_index] <= rx_safe; // Guardar bit
                        
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1;
                        end else begin
                            bit_index <= 0;
                            state <= STOP_BIT;
                        end
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                // 4. Esperar el Stop Bit (Debe ser 1)
                STOP_BIT: begin
                    if (clk_count == CLKS_PER_BIT) begin
                        state <= CLEANUP; // Dato completado
                        data_ready <= 1'b1; // Avisar al sistema
                        clk_count <= 0;
                    end else begin
                        clk_count <= clk_count + 1;
                    end
                end

                // 5. Volver a IDLE
                CLEANUP: begin
                    data_ready <= 0;
                    state <= IDLE;
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule