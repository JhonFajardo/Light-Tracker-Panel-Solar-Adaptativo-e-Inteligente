module bt_data_parser_v2 (
    input wire clk,
    input wire rst_n,
    input wire rx_done_tick,
    input wire [7:0] rx_data,
    
    // Salidas Pantalla 1 (Azimut/Elev)
    output reg [7:0] az_h, output reg [7:0] az_t, output reg [7:0] az_u,
    output reg [7:0] el_t, output reg [7:0] el_u, 
    
    // Salidas Pantalla 2 (Hora y Zona)
    output reg [7:0] time_h1, output reg [7:0] time_h0,
    output reg [7:0] time_m1, output reg [7:0] time_m0,
    output reg [7:0] time_s1, output reg [7:0] time_s0,
    output reg [7:0] zone_id 
);

    // Estados
    localparam IDLE = 0, GET_AZ_1 = 1, GET_AZ_2 = 2, GET_AZ_3 = 3;
    localparam WAIT_E = 4, GET_EL_1 = 5, GET_EL_2 = 6, GET_EL_3 = 7;
    localparam WAIT_H = 8;
    localparam GET_H1 = 9, GET_H0 = 10, GET_M1 = 11, GET_M0 = 12, GET_S1 = 13, GET_S0 = 14;
    localparam WAIT_I = 15, GET_ID = 16, UPDATE = 17;

    reg [4:0] state;
    
    // Buffers temporales
    reg [7:0] b_ah, b_at, b_au, b_et, b_eu; 
    reg [7:0] b_th1, b_th0, b_tm1, b_tm0, b_ts1, b_ts0, b_zid;

    // Inicialización para evitar latches indeseados
    initial begin
        state = IDLE;
        az_h="0"; az_t="0"; az_u="0"; el_t="0"; el_u="0";
        time_h1="0"; time_h0="0"; time_m1="0"; time_m0="0"; time_s1="0"; time_s0="0";
        zone_id="1";
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            // Lógica de transición de estados
            if (state == UPDATE) begin
                // Actualizar salidas y volver a IDLE inmediatamente
                az_h <= b_ah; az_t <= b_at; az_u <= b_au;
                el_t <= b_et; el_u <= b_eu;
                time_h1 <= b_th1; time_h0 <= b_th0;
                time_m1 <= b_tm1; time_m0 <= b_tm0;
                time_s1 <= b_ts1; time_s0 <= b_ts0;
                zone_id <= b_zid;
                state <= IDLE;
            end 
            else if (rx_done_tick) begin
                // Solo avanzamos si llega un dato nuevo UART
                case (state)
                    IDLE: if (rx_data == "A") state <= GET_AZ_1;
                    
                    GET_AZ_1: begin b_ah <= rx_data; state <= GET_AZ_2; end
                    GET_AZ_2: begin b_at <= rx_data; state <= GET_AZ_3; end
                    GET_AZ_3: begin b_au <= rx_data; state <= WAIT_E; end
                    
                    WAIT_E: if (rx_data == "E") state <= GET_EL_1; else state <= IDLE;
                    
                    GET_EL_1: state <= GET_EL_2; // Ignoramos centena elevación
                    GET_EL_2: begin b_et <= rx_data; state <= GET_EL_3; end
                    GET_EL_3: begin b_eu <= rx_data; state <= WAIT_H; end
                    
                    WAIT_H: if (rx_data == "H") state <= GET_H1; else state <= IDLE;
                    
                    GET_H1: begin b_th1 <= rx_data; state <= GET_H0; end
                    GET_H0: begin b_th0 <= rx_data; state <= GET_M1; end
                    GET_M1: begin b_tm1 <= rx_data; state <= GET_M0; end
                    GET_M0: begin b_tm0 <= rx_data; state <= GET_S1; end
                    GET_S1: begin b_ts1 <= rx_data; state <= GET_S0; end
                    GET_S0: begin b_ts0 <= rx_data; state <= WAIT_I; end

                    WAIT_I: if (rx_data == "I") state <= GET_ID; else state <= IDLE;
                    GET_ID: begin b_zid <= rx_data; state <= UPDATE; end
                    
                    default: state <= IDLE;
                endcase
            end
        end
    end
endmodule