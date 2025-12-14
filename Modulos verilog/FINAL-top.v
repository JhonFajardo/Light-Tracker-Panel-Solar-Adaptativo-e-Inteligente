module SolarTracker_Top (
    input wire clk,             // 50 MHz
    input wire rst_n,           // Reset (Activo bajo)
    input wire uart_rxd,        // RX Bluetooth
    
    output wire lcd_rs, lcd_rw, lcd_en,
    output wire [7:0] lcd_data,
    
    output wire servo_azimut,   
    output wire servo_elevacion,
    
    output wire led_rx          
);

    wire rx_ready;
    wire [7:0] rx_byte;
    
    wire [7:0] w_az_h, w_az_t, w_az_u; 
    wire [7:0] w_el_t, w_el_u;         
    wire [7:0] w_th1, w_th0, w_tm1, w_tm0, w_ts1, w_ts0;
    wire [7:0] w_zone;

    // 1. UART
    uart_rx #(.CLK_FREQ(50000000), .BAUD_RATE(9600)) uart (
        .clk(clk), .rst_n(rst_n),
        .rx_serial(uart_rxd),
        .data_ready(rx_ready), .data_byte(rx_byte)
    );
    assign led_rx = rx_ready; 

    // 2. Parser V2
    bt_data_parser_v2 parser (
        .clk(clk), .rst_n(rst_n),
        .rx_done_tick(rx_ready), .rx_data(rx_byte),
        .az_h(w_az_h), .az_t(w_az_t), .az_u(w_az_u),
        .el_t(w_el_t), .el_u(w_el_u),
        .time_h1(w_th1), .time_h0(w_th0),
        .time_m1(w_tm1), .time_m0(w_tm0),
        .time_s1(w_ts1), .time_s0(w_ts0),
        .zone_id(w_zone)
    );

    // 3. Conversión ASCII a Entero
    wire [15:0] azimut_input;
    wire [15:0] elevacion_input;

    assign azimut_input = ((w_az_h - 8'd48) * 100) + ((w_az_t - 8'd48) * 10) + (w_az_u - 8'd48);
    assign elevacion_input = ((w_el_t - 8'd48) * 10) + (w_el_u - 8'd48);

    // 4. Escalado de Servos
    reg [7:0] servo_pos_az;
    reg [7:0] servo_pos_el;

    always @(*) begin
        // --- AZIMUT ---
        // Python ahora envía un valor mapeado de 0 a 270.
        // El servo espera un valor de 0 a 255.
        // Fórmula: (Input * 255) / 270
        if (azimut_input >= 270) 
            servo_pos_az = 8'd255;
        else 
            servo_pos_az = (azimut_input * 255) / 270;


        // --- ELEVACIÓN (REVERTIDO A COMPORTAMIENTO ORIGINAL) ---
        // Aquí mapeamos 0-180 grados de entrada al rango completo del servo (0-255).
        // Como la elevación solar solo llega hasta 90, esto usará la MITAD del servo (bastante movimiento).
        // Antes intenté mapear a 270 y eso redujo el movimiento a 1/3.
        if (elevacion_input >= 180)
            servo_pos_el = 8'd255;
        else
            servo_pos_el = (elevacion_input * 255) / 180;
    end

    // --- 5. CONTROLADORES CON SUAVIZADO ---
    
    // AZIMUT
    servo_pwm_smooth #(
        .CLK_FREQ_HZ(50000000), .PERIOD_MS(20),
        .MIN_PULSE_US(500), .MAX_PULSE_US(2500), // Rango 270 grados
        .SMOOTH_DELAY_MS(10)
    ) servo_h (
        .clk(clk), .reset(~rst_n),       
        .target_pos(servo_pos_az),
        .pwm_out(servo_azimut)
    );

    // ELEVACIÓN
    servo_pwm_smooth #(
        .CLK_FREQ_HZ(50000000), .PERIOD_MS(20),
        .MIN_PULSE_US(500), .MAX_PULSE_US(2500), // Rango 270 grados
        .SMOOTH_DELAY_MS(10) 
    ) servo_v (
        .clk(clk), .reset(~rst_n),
        .target_pos(servo_pos_el),
        .pwm_out(servo_elevacion)
    );

    // 6. LCD
    LCD1602_DualScreen lcd (
        .clk(clk), .reset(rst_n),
        .az_h(w_az_h), .az_t(w_az_t), .az_u(w_az_u),
        .el_t(w_el_t), .el_u(w_el_u),
        .t_h1(w_th1), .t_h0(w_th0),
        .t_m1(w_tm1), .t_m0(w_tm0),
        .t_s1(w_ts1), .t_s0(w_ts0),
        .zone_id_ascii(w_zone),
        .rs(lcd_rs), .rw(lcd_rw), .enable(lcd_en), .data(lcd_data)
    );

endmodule