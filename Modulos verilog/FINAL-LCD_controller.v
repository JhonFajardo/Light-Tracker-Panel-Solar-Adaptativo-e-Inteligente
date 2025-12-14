module LCD1602_DualScreen #(
    parameter DATA_BITS = 8
)(
    input clk,
    input reset,
    
    // Datos Pantalla 1
    input [7:0] az_h, input [7:0] az_t, input [7:0] az_u,
    input [7:0] el_t, input [7:0] el_u,
    
    // Datos Pantalla 2
    input [7:0] t_h1, input [7:0] t_h0, 
    input [7:0] t_m1, input [7:0] t_m0,
    input [7:0] t_s1, input [7:0] t_s0,
    input [7:0] zone_id_ascii,

    output reg rs, output reg rw, output enable,
    output reg [DATA_BITS-1:0] data
);

    localparam BOOT=0, IDLE=1, STATIC_1=2, STATIC_2=3, DYN_MAIN=4;

    reg [2:0] state;
    reg [4:0] cnt; 
    reg clk_16ms;
    reg [19:0] clk_div;
    
    always @(posedge clk) begin
        if(clk_div >= 800000) begin 
            clk_div <= 0; 
            clk_16ms <= ~clk_16ms; 
        end else 
            clk_div <= clk_div + 1;
    end

    reg current_screen;
    reg [7:0] timer_seconds; 

    always @(posedge clk_16ms or negedge reset) begin
        if (!reset) begin
            state <= BOOT;
            cnt <= 0;
            rs <= 0; rw <= 0; data <= 0;
            current_screen <= 0;
            timer_seconds <= 0;
        end else begin
            case (state)
                BOOT: begin
                    rs <= 0;
                    case (cnt)
                        0: data <= 8'h38; 
                        1: data <= 8'h0C; 
                        2: data <= 8'h06; 
                        3: begin state <= IDLE; cnt <= 0; end
                    endcase
                    if (cnt < 3) cnt <= cnt + 1;
                end

                IDLE: begin 
                    rs <= 0; data <= 8'h01; 
                    state <= STATIC_1; cnt <= 0;
                end
                
                STATIC_1: begin
                    rs <= 1;
                    if (current_screen == 0) begin
                        case(cnt)
                            0: data <= "A"; 1: data <= "z"; 2: data <= "i";
                            3: data <= "m"; 4: data <= "u"; 5: data <= "t";
                            6: data <= ":"; default: data <= " "; 
                        endcase
                        if (cnt < 9) cnt <= cnt + 1; else begin rs <= 0; data <= 8'hC0; state <= STATIC_2; cnt <= 0; end
                    end else begin
                        case(cnt)
                            0: data <= "Z"; 1: data <= "o"; 2: data <= "n";
                            3: data <= "a"; 4: data <= ":"; default: data <= " ";
                        endcase
                        if (cnt < 5) cnt <= cnt + 1; else begin rs <= 0; data <= 8'hC0; state <= STATIC_2; cnt <= 0; end
                    end
                end

                STATIC_2: begin
                    rs <= 1;
                    if (current_screen == 0) begin
                        case(cnt)
                            0: data <= "E"; 1: data <= "l"; 2: data <= "e";
                            3: data <= "v"; 4: data <= "a"; 5: data <= "c";
                            6: data <= "i"; 7: data <= "o"; 8: data <= "n";
                            9: data <= ":"; default: data <= " ";
                        endcase
                        if (cnt < 9) cnt <= cnt + 1; else begin state <= DYN_MAIN; cnt <= 0; end
                    end else begin
                        case(cnt)
                            0: data <= "H"; 1: data <= "o"; 2: data <= "r";
                            3: data <= "a"; 4: data <= ":"; default: data <= " ";
                        endcase
                        if (cnt < 5) cnt <= cnt + 1; else begin state <= DYN_MAIN; cnt <= 0; end
                    end
                end

                DYN_MAIN: begin
                    if (current_screen == 0) begin
                        if (cnt == 0) begin rs<=0; data <= 8'h80 + 10; end 
                        else if (cnt >= 1 && cnt <= 3) begin
                            rs<=1; 
                            if(cnt==1) data<=az_h; else if(cnt==2) data<=az_t; else if(cnt==3) data<=az_u; else data <= " "; 
                        end
                        else if (cnt == 4) begin rs<=0; data <= 8'hC0 + 10; end 
                        else if (cnt >= 5 && cnt <= 6) begin
                            rs<=1;
                            if(cnt==5) data<=el_t; else if(cnt==6) data<=el_u; else data <= " "; 
                        end
                        else if (cnt == 7) begin rs<=1; data <= " "; end

                        if (cnt < 7) cnt <= cnt + 1; else cnt <= 0;

                    end else begin
                        if (cnt == 0) begin rs<=0; data <= 8'h80 + 6; end
                        else if (cnt >= 1 && cnt <= 8) begin 
                            rs<=1;
                            // --- MODIFICACIÓN AQUÍ ---
                            case (zone_id_ascii)
                                "1": case(cnt) 1: data<="B"; 2: data<="o"; 3: data<="g"; 4: data<="o"; 5: data<="t"; 6: data<="a"; default: data<=" "; endcase
                                "2": case(cnt) 1: data<="M"; 2: data<="a"; 3: data<="d"; 4: data<="r"; 5: data<="i"; 6: data<="d"; default: data<=" "; endcase
                                "3": case(cnt) 1: data<="S"; 2: data<="y"; 3: data<="d"; 4: data<="n"; 5: data<="e"; 6: data<="y"; default: data<=" "; endcase
                                "4": case(cnt) 1: data<="T"; 2: data<="o"; 3: data<="k"; 4: data<="i"; 5: data<="o"; default: data<=" "; endcase
                                "5": case(cnt) 1: data<="A"; 2: data<="l"; 3: data<="a"; 4: data<="s"; 5: data<="k"; 6: data<="a"; default: data<=" "; endcase
                                "6": case(cnt) 1: data<="P"; 2: data<="o"; 3: data<="l"; 4: data<="o"; 5: data<=" "; 6: data<="S"; default: data<=" "; endcase
                                
                                // --- NUEVO CASO MANUAL ---
                                "7": case(cnt) 1: data<="M"; 2: data<="A"; 3: data<="N"; 4: data<="U"; 5: data<="A"; 6: data<="L"; default: data<=" "; endcase
                                
                                default: data <= " ";
                            endcase
                            // -------------------------
                        end
                        else if (cnt == 9) begin rs<=0; data <= 8'hC0 + 6; end
                        else if (cnt >= 10 && cnt <= 17) begin
                            rs<=1;
                            case(cnt)
                                10: data <= t_h1; 11: data <= t_h0;
                                12: data <= ":";
                                13: data <= t_m1; 14: data <= t_m0;
                                15: data <= ":";
                                16: data <= t_s1; 17: data <= t_s0;
                                default: data <= " "; 
                            endcase
                        end
                        if (cnt < 17) cnt <= cnt + 1; else cnt <= 0;
                    end

                    if (cnt == 0) begin
                        timer_seconds <= timer_seconds + 1;
                        if (timer_seconds >= 20) begin 
                            timer_seconds <= 0;
                            current_screen <= ~current_screen;
                            state <= IDLE;
                        end
                    end
                end
            endcase
        end
    end

    assign enable = clk_16ms;

endmodule