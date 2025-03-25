use std::collections::HashMap;
use actix_web::{web, App, HttpServer, Responder, HttpResponse};
use regex::Regex;
use serde::*;
use postflop_solver::*;

#[derive(Deserialize)]  // 用于反序列化请求中的 JSON 数据
struct GetGtoRequest {
    user_spt: String,       // required
    opponent_spt: String,   // required
    flop: String,           // required
    turn: Option<String>,   // optional, default to Some(NOT_DEALT)
    river: Option<String>,  // optional, default to Some(NOT_DEALT)
    effective_stk: Option<i32>, // optional
    pot: Option<i32>,           // optional
    actions: Vec<String>,   // ["Check", "Bet(120)", "Bet(216)", "AllIn(900)"]
    user_hand: String,      // required
}

#[derive(Serialize)]
struct GtoResponse {
    available_actions_probability: Vec<f32>,     //[0.6,0.1,0.3]
    available_actions: Vec<String>,             //["Check", "Bet(120)", "Bet(216)"]
    opponent_hands_range: Vec<String>,          //["AsAh", "AsAd", "AsAc"]
    opponent_hands_ev: Vec<f32>,                //[-0.1, 0.2, 0.3]
    opponent_hands_weights: Vec<f32>,           //expected_values_detail
}

fn determine_position<'a>(
    user_spt: &'a str,
    opponent_spt: &'a str,
) -> (&'a str, &'a str, usize, usize) {
    let positions = vec!["SB", "BB", "UTG", "UTG+1", "MP", "MP+1", "CO", "BTN"];

    let user_index = positions.iter().position(|&x| x == user_spt).unwrap_or_else(|| {
        panic!("Invalid user_spt: {}", user_spt);
    });
    let opponent_index = positions.iter().position(|&x| x == opponent_spt).unwrap_or_else(|| {
        panic!("Invalid opponent_spt: {}", opponent_spt);
    });

    if user_index > opponent_index {
        // user is IP
        (user_spt, opponent_spt, 1, 0)
    } else {
        // opponent is IP
        (opponent_spt, user_spt, 0, 1)
    }
}

async fn get_gto(data: web::Json<GetGtoRequest>) -> impl Responder {

    let turn = data.turn.as_ref()
    .map(|s| card_from_str(s).unwrap_or(NOT_DEALT))
    .unwrap_or(NOT_DEALT);

    let river = data.river.as_ref()
    .map(|s| card_from_str(s).unwrap_or(NOT_DEALT))
    .unwrap_or(NOT_DEALT);
    let effective_stk = data.effective_stk.unwrap_or(100);
    let pot = data.pot.unwrap_or(10);


    let mut hand_ranges: HashMap<&str, &str> = HashMap::new();
    hand_ranges.insert("UTG", "77+,AJs+,ATs+,KQs,AKo");
    hand_ranges.insert("UTG+1", "66+,A9s+,ATs+,KQs,AKo");
    hand_ranges.insert("MP", "55+,A8s+,A9s+,ATs+,KQs,KJs,AKo,AJo");
    hand_ranges.insert("MP+1", "44+,A7s+,A8s+,A9s+,ATs+,KQs,KJs,QTs,AKo,AJo,KQo");
    hand_ranges.insert("CO", "22+,A2s+,A3s+,A4s+,A5s+,A6s+,A7s+,A8s+,A9s+,ATs+,K2s+,K3s+,K4s+,K5s+,K6s+,K7s+,K8s+,K9s+,Q2s+,Q3s+,Q4s+,Q5s+,Q6s+,Q7s+,Q8s+,Q9s+,J2s+,J3s+,J4s+,J5s+,J6s+,J7s+,J8s+,J9s+,T2s+,T3s+,T4s+,T5s+,T6s+,T7s+,T8s+,T9s,65s+,54s+,43s+,32s+,A2o+,A3o+,A4o+,A5o+,A6o+,A7o+,A8o+,A9o+,ATo+,K2o+,K3o+,K4o+,K5o+,K6o+,K7o+,K8o+,K9o+,Q2o+,Q3o+,Q4o+,Q5o+,Q6o+,Q7o+,Q8o+,Q9o+,J2o+,J3o+,J4o+,J5o+,J6o+,J7o+,J8o+,J9o,T2o+,T3o+,T4o+,T5o+,T6o+,T7o+,T8o+,T9o");
    hand_ranges.insert("BTN", "22+,A2s+,A3s+,A4s+,A5s+,A6s+,A7s+,A8s+,A9s+,ATs+,K2s+,K3s+,K4s+,K5s+,K6s+,K7s+,K8s+,K9s+,Q2s+,Q3s+,Q4s+,Q5s+,Q6s+,Q7s+,Q8s+,Q9s+,J2s+,J3s+,J4s+,J5s+,J6s+,J7s+,J8s+,J9s+,T2s+,T3s+,T4s+,T5s+,T6s+,T7s+,T8s+,T9s,65s+,54s+,43s+,32s+,A2o+,A3o+,A4o+,A5o+,A6o+,A7o+,A8o+,A9o+,ATo+,K2o+,K3o+,K4o+,K5o+,K6o+,K7o+,K8o+,K9o+,Q2o+,Q3o+,Q4o+,Q5o+,Q6o+,Q7o+,Q8o+,Q9o+,J2o+,J3o+,J4o+,J5o+,J6o+,J7o+,J8o+,J9o,T2o+,T3o+,T4o+,T5o+,T6o+,T7o+,T8o+,T9o");
    hand_ranges.insert("SB", "22+,A2s+,A3s+,A4s+,A5s+,A6s+,A7s+,A8s+,A9s+,ATs+,K2s+,K3s+,K4s+,K5s+,K6s+,K7s+,K8s+,K9s+,Q2s+,Q3s+,Q4s+,Q5s+,Q6s+,Q7s+,Q8s+,Q9s+,J2s+,J3s+,J4s+,J5s+,J6s+,J7s+,J8s+,J9s+,T2s+,T3s+,T4s+,T5s+,T6s+,T7s+,T8s+,T9s,65s+,54s+,43s+,32s+,A2o+,A3o+,A4o+,A5o+,A6o+,A7o+,A8o+,A9o+,ATo+,K2o+,K3o+,K4o+,K5o+,K6o+,K7o+,K8o+,K9o+,Q2o+,Q3o+,Q4o+,Q5o+,Q6o+,Q7o+,Q8o+,Q9o+,J2o+,J3o+,J4o+,J5o+,J6o+,J7o+,J8o+,J9o,T2o+,T3o+,T4o+,T5o+,T6o+,T7o+,T8o+,T9o");
    hand_ranges.insert("BB", "22+,A2s+,A3s+,A4s+,A5s+,A6s+,A7s+,A8s+,A9s+,ATs+,K2s+,K3s+,K4s+,K5s+,K6s+,K7s+,K8s+,K9s+,Q2s+,Q3s+,Q4s+,Q5s+,Q6s+,Q7s+,Q8s+,Q9s+,J2s+,J3s+,J4s+,J5s+,J6s+,J7s+,J8s+,J9s+,T2s+,T3s+,T4s+,T5s+,T6s+,T7s+,T8s+,T9s,65s+,54s+,43s+,32s+,A2o+,A3o+,A4o+,A5o+,A6o+,A7o+,A8o+,A9o+,ATo+,K2o+,K3o+,K4o+,K5o+,K6o+,K7o+,K8o+,K9o+,Q2o+,Q3o+,Q4o+,Q5o+,Q6o+,Q7o+,Q8o+,Q9o+,J2o+,J3o+,J4o+,J5o+,J6o+,J7o+,J8o+,J9o,T2o+,T3o+,T4o+,T5o+,T6o+,T7o+,T8o+,T9o");

    let (ip_spt, opp_spt, user_index, opponent_index) = determine_position(&data.user_spt, &data.opponent_spt);
    let oop_range = hand_ranges[opp_spt];
    let ip_range = hand_ranges[ip_spt];
    
    let card_config = CardConfig {
        range: [oop_range.parse().unwrap(), ip_range.parse().unwrap()],
        flop: flop_from_str(&data.flop).unwrap(),
        turn: turn,
        river: NOT_DEALT
    };

    let bet_sizes = BetSizeOptions::try_from(("60%, e, a", "2.5x")).unwrap();
    
    let tree_config = TreeConfig {
        initial_state: BoardState::Turn, // must match `card_config`
        starting_pot: pot,
        effective_stack: effective_stk,
        rake_rate: 0.0,
        rake_cap: 0.0,
        flop_bet_sizes: [bet_sizes.clone(), bet_sizes.clone()], // [OOP, IP]
        turn_bet_sizes: [bet_sizes.clone(), bet_sizes.clone()],
        river_bet_sizes: [bet_sizes.clone(), bet_sizes],
        turn_donk_sizes: None, // use default bet sizes
        river_donk_sizes: Some(DonkSizeOptions::try_from("50%").unwrap()),
        add_allin_threshold: 1.5, // add all-in if (maximum bet size) <= 1.5x pot
        force_allin_threshold: 0.15, // force all-in if (SPR after the opponent's call) <= 0.15
        merging_threshold: 0.1,
    };

    let action_tree = ActionTree::new(tree_config).unwrap();
    let mut game = PostFlopGame::with_config(card_config, action_tree).unwrap();
    
    let (mem_usage, mem_usage_compressed) = game.memory_usage();
    println!(
        "Memory usage without compression (32-bit float): {:.2}GB",
        mem_usage as f64 / (1024.0 * 1024.0 * 1024.0)
    );
    println!(
        "Memory usage with compression (16-bit integer): {:.2}GB",
        mem_usage_compressed as f64 / (1024.0 * 1024.0 * 1024.0)
    );

    // allocate memory without compression (use 32-bit float)
    game.allocate_memory(false);
    // solve the game
    let max_num_iterations = 1000;
    let target_exploitability = game.tree_config().starting_pot as f32 * 0.005; // 0.5% of the pot
    let exploitability = solve(&mut game, max_num_iterations, target_exploitability, true);
    println!("Exploitability: {:.2}", exploitability);
    game.cache_normalized_weights();
    let equity = game.equity(0); // `0` means OOP player
    let ev = game.expected_values(0);
    println!("Equity of oop_hands[0]: {:.2}%", 100.0 * equity[0]);
    println!("EV of oop_hands[0]: {:.2}", ev[0]);

    // get equity and EV of whole hand
    let weights = game.normalized_weights(0);
    let average_equity = compute_average(&equity, weights);
    let average_ev = compute_average(&ev, weights);
    println!("Average equity: {:.2}%", 100.0 * average_equity);
    println!("Average EV: {:.2}", average_ev);
    // let available_actions = game.available_actions();
    // println!("Available Actions: {:?}", available_actions);
    println!("Received actions: {:?}", data.actions);

    // Regex to extract amount from "Bet(x)", "Raise(x)", "AllIn(x)"
    let bet_regex = Regex::new(r"^(Bet|Raise|AllIn)\((\d+)\)$").unwrap();

    let parsed_actions: Vec<(String, Option<i32>)> = data.actions.iter().map(|act| {
        if act == "turn" || act == "river" {
            (act.clone(), None)
        } else if let Some(caps) = bet_regex.captures(act) {
            let action_type = caps[1].to_string();
            let amount = caps[2].parse::<i32>().ok();
            (action_type, amount)
        } else {
            (act.clone(), None)
        }
    }).collect();

    println!("Parsed Actions: {:?}", parsed_actions);

    let mut selected_actions = Vec::new();

    for (action_str, amount) in parsed_actions {
        if action_str == "turn" {
            if let Some(card_str) = &data.turn {
                let card = card_from_str(card_str).unwrap();
                println!("Dealing turn card: {}", card_str);
                game.play(card as usize);
            } else {
                println!("Turn card missing in input data");
            }
            continue;
        }
    
        if action_str == "river" {
            if let Some(card_str) = &data.river {
                let card = card_from_str(card_str).unwrap();
                println!("Dealing river card: {}", card_str);
                game.play(card as usize);
            } else {
                println!("River card missing in input data");
            }
            continue;
        }
    
        let available_actions = game.available_actions();
        println!("available_actions: {:?}", available_actions);
    
        let best_match = match action_str.as_str() {
            "Fold" => available_actions.iter().position(|a| matches!(a, Action::Fold)),
            "Call" => available_actions.iter().position(|a| matches!(a, Action::Call)),
            "Check" => available_actions.iter().position(|a| matches!(a, Action::Check)),
            "Bet" | "Raise" | "AllIn" => {
                let mut closest = None;
                let mut min_diff = i32::MAX;
                for (i, a) in available_actions.iter().enumerate() {
                    if let Some(av_amount) = extract_bet_amount(a) {
                        if let Some(user_amount) = amount {
                            let diff = (av_amount - user_amount).abs();
                            if diff < min_diff {
                                min_diff = diff;
                                closest = Some(i);
                            }
                        }
                    }
                }
                closest
            }
            _ => {
                println!("Unknown action: {:?}", action_str);
                None
            }
        };
    
        if let Some(index) = best_match {
            println!(
                "User action: {:?}({:?}), Closest available action: {:?}",
                action_str, amount, available_actions[index]
            );
            selected_actions.push(format!(
                "User action: {}({:?}), Selected: {:?}",
                action_str, amount, available_actions[index]
            ));
            game.play(index);
        } else {
            println!("No matching action found for {:?}", action_str);
        }
    }

    game.cache_normalized_weights();

    let opponent_hands_range = holes_to_strings(game.private_cards(opponent_index)).unwrap();
    let opponent_hands_ev = game.expected_values(opponent_index);
    let opponent_hands_weights = game.weights(opponent_index).to_vec();

    let available_actions = game.available_actions();

    let available_action_strings: Vec<String> = available_actions
    .iter()
    .map(|action| match action {
        Action::Fold => "Fold".to_string(),
        Action::Check => "Check".to_string(),
        Action::Call => "Call".to_string(),
        Action::Bet(amount) => format!("Bet({})", amount),
        Action::Raise(amount) => format!("Raise({})", amount),
        Action::AllIn(amount) => format!("AllIn({})", amount),
        Action::Chance(card) => format!("Chance({:?})", card),
        Action::None => "None".to_string(),
    })
    .collect();

    let user_cards = game.private_cards(user_index);

    let hand_index = holes_to_strings(user_cards)
        .unwrap()
        .iter()
        .position(|s| *s == data.user_hand)
        .unwrap();

    let strategy = game.strategy();
    let num_actions = available_actions.len();
    let private_hands_len = game.private_cards(user_index).len();

    let available_actions_probability: Vec<f32> = (0..num_actions)
    .map(|i| strategy[i * private_hands_len + hand_index])
    .collect();

    println!("opponent_hands_ev.len() = {}", opponent_hands_ev.len());
    println!("opponent_hands_range.len() = {}", opponent_hands_range.len());

    let response = GtoResponse {
        available_actions_probability,
        available_actions : available_action_strings,
        opponent_hands_range,
        opponent_hands_ev,
        opponent_hands_weights,
    };

    // let response = format!(
    //     "Received GTO with userSpt: {}, opponentSpt: {}\nAvailable Actions: {:?}\nSelected Actions:\n{}",
    //     data.user_spt,
    //     data.opponent_spt,
    //     available_actions,
    //     selected_actions.join("\n")
    // );

    HttpResponse::Ok().json(response)
}

// 辅助函数：提取可用 action 的下注金额
fn extract_bet_amount(action: &Action) -> Option<i32> {
    match action {
        Action::Bet(amount) | Action::Raise(amount) | Action::AllIn(amount) => Some(*amount),
        _ => None,
    }
}
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/demo/getGto", web::post().to(get_gto))  // 使用 POST 请求
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
