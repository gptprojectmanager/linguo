use eframe::egui::{self, Color32, FontFamily, RichText, Stroke, Vec2};
use rusqlite::{params, Connection};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct LinguoCard {
    pub id: i64,
    pub created_at: String,
    pub error_category: String,
    pub sprite_name: String,
    pub card_title: String,
    pub cefr_level: String,
    pub card_type: String,
    pub front_challenge: String,
    pub back_solution: String,
    pub british_council_rule: String,
    pub gag_quote: String,
    pub thai_script: String,
    pub thai_phonetic: String,
    pub thai_tones: String,
    pub thai_breakdown: String,
    pub source_history_ids: String,
    pub is_mastered: bool,
    pub is_revealed: bool,
}

struct LinguoGuiApp {
    cards: Vec<LinguoCard>,
    current_index: usize,
    show_mastered: bool,
    is_pinned: bool,
    status_message: Option<(String, Instant)>,
    db_path: PathBuf,
}

impl LinguoGuiApp {
    fn new(cc: &eframe::CreationContext<'_>) -> Self {
        // Setup retro arcade fonts with Thai support
        let mut fonts = egui::FontDefinitions::default();
        if let Ok(font_bytes) = std::fs::read("/System/Library/Fonts/Supplemental/Ayuthaya.ttf") {
            fonts.font_data.insert(
                "ayuthaya".to_owned(),
                egui::FontData::from_owned(font_bytes),
            );
            if let Some(family) = fonts.families.get_mut(&FontFamily::Proportional) {
                family.insert(0, "ayuthaya".to_owned());
            }
            if let Some(family) = fonts.families.get_mut(&FontFamily::Monospace) {
                family.insert(0, "ayuthaya".to_owned());
            }
        }
        cc.egui_ctx.set_fonts(fonts);

        let db_path = get_db_path();
        let mut app = Self {
            cards: Vec::new(),
            current_index: 0,
            show_mastered: false,
            is_pinned: false,
            status_message: None,
            db_path,
        };
        app.reload_cards();
        app
    }


    fn reload_cards(&mut self) {
        match load_cards_from_db(&self.db_path) {
            Ok(loaded) => {
                self.cards = loaded;
                let count = self.visible_cards().len();
                if self.current_index >= count && count > 0 {
                    self.current_index = count - 1;
                }
                self.set_status("Deck reloaded from SQLite database");
            }
            Err(e) => {
                self.set_status(format!("DB Load Error: {}", e));
            }
        }
    }

    fn visible_cards(&self) -> Vec<&LinguoCard> {
        self.cards
            .iter()
            .filter(|c| self.show_mastered || !c.is_mastered)
            .collect()
    }

    fn visible_card_mut_id(&self) -> Option<i64> {
        let v = self.visible_cards();
        v.get(self.current_index).map(|c| c.id)
    }

    fn set_status<S: Into<String>>(&mut self, msg: S) {
        self.status_message = Some((msg.into(), Instant::now()));
    }

    fn toggle_master(&mut self) {
        let mut status_to_set = None;
        if let Some(card_id) = self.visible_card_mut_id() {
            if let Some(card) = self.cards.iter_mut().find(|c| c.id == card_id) {
                let new_val = !card.is_mastered;
                card.is_mastered = new_val;
                let _ = set_card_mastered_in_db(&self.db_path, card.id, new_val);
                let title = card.card_title.clone();
                status_to_set = Some(if new_val {
                    format!("🏆 Mastered: {}", title)
                } else {
                    format!("Active again: {}", title)
                });
            }
        }
        if let Some(st) = status_to_set {
            self.set_status(st);
        }
    }

    fn play_audio_english(&mut self) {
        if let Some(card_id) = self.visible_card_mut_id() {
            if let Some(card) = self.cards.iter().find(|c| c.id == card_id) {
                let db_path = self.db_path.clone();
                let source_ids = card.source_history_ids.clone();
                let solution_text = card.back_solution.clone();
                self.set_status("Playing English audio (Nicole 0.8x / Samantha)...");

                std::thread::spawn(move || {
                    let mut played = false;
                    if let Ok(conn) = Connection::open(&db_path) {
                        let first_id = source_ids.split(',').next().unwrap_or("").trim();
                        if let Ok(id_num) = first_id.parse::<i64>() {
                            let stmt = conn.prepare("SELECT audio_eng_path FROM history WHERE id = ?").ok();
                            if let Some(mut s) = stmt {
                                if let Ok(mut rows) = s.query([id_num]) {
                                    if let Ok(Some(row)) = rows.next() {
                                        let p: Option<String> = row.get(0).ok();
                                        if let Some(path_str) = p {
                                            if Path::new(&path_str).exists() {
                                                let _ = Command::new("afplay").arg(&path_str).status();
                                                played = true;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if !played {
                        let _ = Command::new("say").args(["-v", "Samantha", "-r", "165", &solution_text]).status();
                    }
                });
            }
        }
    }

    fn play_audio_thai(&mut self) {
        if let Some(card_id) = self.visible_card_mut_id() {
            if let Some(card) = self.cards.iter().find(|c| c.id == card_id) {
                let thai_text = card.thai_script.clone();
                self.set_status(format!("Playing Thai audio: {}...", thai_text));

                std::thread::spawn(move || {
                    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
                    let cache_dir = PathBuf::from(home).join(".local/share/linguo/cache/thai");
                    let hash = format!("{:x}", md5::compute(format!("{}_0.8", thai_text.trim()).as_bytes()));
                    let cached_file = cache_dir.join(format!("{}.mp3", hash));

                    if cached_file.exists() {
                        let _ = Command::new("afplay").arg(&cached_file).status();
                    } else {
                        let _ = Command::new("say").args(["-v", "Kanya", "-r", "150", &thai_text]).status();
                    }
                });
            }
        }
    }
}

impl eframe::App for LinguoGuiApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Global Keyboard Controls
        ctx.input(|i| {
            if i.key_pressed(egui::Key::Space) {
                if let Some(card_id) = self.visible_card_mut_id() {
                    if let Some(card) = self.cards.iter_mut().find(|c| c.id == card_id) {
                        card.is_revealed = !card.is_revealed;
                    }
                }
            }
            if i.key_pressed(egui::Key::ArrowLeft) || i.key_pressed(egui::Key::A) {
                let count = self.visible_cards().len();
                if count > 0 {
                    self.current_index = (self.current_index + count - 1) % count;
                }
            }
            if i.key_pressed(egui::Key::ArrowRight) || i.key_pressed(egui::Key::D) {
                let count = self.visible_cards().len();
                if count > 0 {
                    self.current_index = (self.current_index + 1) % count;
                }
            }
            if i.key_pressed(egui::Key::E) {
                self.play_audio_english();
            }
            if i.key_pressed(egui::Key::T) || i.key_pressed(egui::Key::R) {
                self.play_audio_thai();
            }
            if i.key_pressed(egui::Key::M) {
                self.toggle_master();
            }
            if i.key_pressed(egui::Key::P) {
                self.is_pinned = !self.is_pinned;
                let level = if self.is_pinned { egui::WindowLevel::AlwaysOnTop } else { egui::WindowLevel::Normal };
                ctx.send_viewport_cmd(egui::ViewportCommand::WindowLevel(level));
                let status = if self.is_pinned { "📌 Window pinned always-on-top" } else { "📍 Window unpinned" };
                self.set_status(status);
            }
            if i.key_pressed(egui::Key::F5) {
                self.reload_cards();
            }
        });

        // Retro Arcade Styling
        let dark_bg = Color32::from_rgb(13, 17, 23);
        let gold = Color32::from_rgb(218, 165, 32);
        let cyan = Color32::from_rgb(0, 229, 255);
        let neon_green = Color32::from_rgb(74, 222, 128);
        let gag_amber = Color32::from_rgb(251, 146, 60);

        egui::CentralPanel::default()
            .frame(egui::Frame::none().fill(dark_bg).inner_margin(16.0))
            .show(ctx, |ui| {
                // Header Bar
                ui.horizontal(|ui| {
                    ui.heading(RichText::new("🎮 LINGUO // ARCADE DECK").color(gold).strong());
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        let pin_lbl = if self.is_pinned { "📌 Pinned" } else { "📍 Pin (P)" };
                        if ui.button(RichText::new(pin_lbl).color(if self.is_pinned { gold } else { Color32::GRAY })).clicked() {
                            self.is_pinned = !self.is_pinned;
                            let level = if self.is_pinned { egui::WindowLevel::AlwaysOnTop } else { egui::WindowLevel::Normal };
                            ctx.send_viewport_cmd(egui::ViewportCommand::WindowLevel(level));
                            let status = if self.is_pinned { "📌 Window pinned always-on-top" } else { "📍 Window unpinned" };
                            self.set_status(status);
                        }
                        if ui.button("🔄 Reload").clicked() {
                            self.reload_cards();
                        }
                        if ui.checkbox(&mut self.show_mastered, "Show Mastered").changed() {
                            self.current_index = 0;
                        }
                    });
                });



                ui.add_space(8.0);

                let total_visible = self.visible_cards().len();

                if total_visible == 0 {
                    egui::Frame::group(ui.style())
                        .fill(Color32::from_rgb(20, 26, 36))
                        .stroke(Stroke::new(1.5, gold))
                        .inner_margin(32.0)
                        .show(ui, |ui| {
                            ui.vertical_centered(|ui| {
                                ui.heading(RichText::new("🏆 ALL CARDS MASTERED!").color(gold).size(22.0));
                                ui.add_space(10.0);
                                ui.label(RichText::new("No active gaps remaining in this deck.").color(Color32::WHITE));
                                ui.label(RichText::new("Speak more English via 'linguo' to detect new gaps, or tick 'Show Mastered' to review.").color(Color32::GRAY));
                            });
                        });
                    return;
                }

                if self.current_index >= total_visible {
                    self.current_index = 0;
                }

                let current_card = self.visible_cards()[self.current_index].clone();

                // Deck Progress Header
                ui.horizontal(|ui| {
                    ui.label(RichText::new(format!("CARD {} OF {}", self.current_index + 1, total_visible)).color(cyan).strong());
                    ui.separator();
                    if current_card.is_mastered {
                        ui.label(RichText::new("⭐ MASTERED").color(gold).strong());
                    } else {
                        ui.label(RichText::new("⚔️ ACTIVE GAP").color(neon_green).strong());
                    }
                    ui.separator();
                    ui.label(RichText::new(format!("CEFR {}", current_card.cefr_level)).color(Color32::LIGHT_GRAY));
                });

                ui.add_space(8.0);

                // MTG ARCADE CARD CONTAINER
                let card_frame = egui::Frame::group(ui.style())
                    .fill(Color32::from_rgb(20, 25, 36))
                    .stroke(Stroke::new(2.5, if current_card.is_revealed { neon_green } else { gold }))
                    .rounding(10.0)
                    .inner_margin(16.0);

                card_frame.show(ui, |ui| {
                    // Card Top Title Bar
                    ui.horizontal(|ui| {
                        let sprite_badge = match current_card.sprite_name.as_str() {
                            "market_stamp" => "🎫",
                            "gerund_vest" => "⚓",
                            "to_toll" => "🪙",
                            _ => "👾",
                        };
                        ui.label(RichText::new(sprite_badge).size(26.0));
                        ui.heading(RichText::new(&current_card.card_title).color(gold).size(20.0).strong());
                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                            ui.label(RichText::new(&current_card.card_type).color(Color32::GRAY).size(12.0));
                        });
                    });

                    ui.separator();
                    ui.add_space(6.0);

                    // Card Main Face: FRONT (Challenge) vs BACK (Solution)
                    if !current_card.is_revealed {
                        // FRONT FACE: ACTIVE RECALL PUZZLE
                        ui.label(RichText::new("⚔️ ACTIVE RECALL CHALLENGE:").color(cyan).strong());
                        ui.add_space(4.0);

                        egui::Frame::none()
                            .fill(Color32::from_rgb(12, 16, 24))
                            .stroke(Stroke::new(1.0, Color32::from_rgb(60, 70, 90)))
                            .rounding(6.0)
                            .inner_margin(14.0)
                            .show(ui, |ui| {
                                ui.label(
                                    RichText::new(&current_card.front_challenge)
                                        .color(Color32::WHITE)
                                        .size(16.0)
                                        .strong(),
                                );
                            });

                        ui.add_space(10.0);
                        ui.label(RichText::new(format!("TARGET GAP: {}", current_card.error_category)).color(Color32::LIGHT_BLUE).size(12.0));
                        ui.add_space(8.0);

                        ui.vertical_centered(|ui| {
                            if ui.button(RichText::new("👉 Click or Press [SPACE] to Reveal Solution").color(gold).size(14.0)).clicked() {
                                if let Some(card_id) = self.visible_card_mut_id() {
                                    if let Some(c) = self.cards.iter_mut().find(|c| c.id == card_id) {
                                        c.is_revealed = true;
                                    }
                                }
                            }
                        });
                    } else {
                        // BACK FACE: SOLUTION & CAMBRIDGE RULE
                        ui.label(RichText::new("🛡️ BRITISH COUNCIL RECTIFICATION:").color(neon_green).strong());
                        ui.add_space(4.0);

                        egui::Frame::none()
                            .fill(Color32::from_rgb(10, 24, 18))
                            .stroke(Stroke::new(1.0, neon_green))
                            .rounding(6.0)
                            .inner_margin(12.0)
                            .show(ui, |ui| {
                                ui.label(
                                    RichText::new(&current_card.back_solution)
                                        .color(neon_green)
                                        .size(16.0)
                                        .strong(),
                                );
                            });

                        ui.add_space(8.0);
                        ui.label(RichText::new("📖 Cambridge / British Council Rule:").color(cyan).strong().size(13.0));
                        ui.label(RichText::new(&current_card.british_council_rule).color(Color32::LIGHT_GRAY).size(13.0));

                        ui.add_space(8.0);
                        // 16-bit Comic Gag Box (ADHD Emotional Anchor)
                        egui::Frame::none()
                            .fill(Color32::from_rgb(28, 22, 14))
                            .stroke(Stroke::new(1.0, gag_amber))
                            .rounding(6.0)
                            .inner_margin(10.0)
                            .show(ui, |ui| {
                                ui.label(RichText::new("🎭 16-bit Arcade Gag:").color(gag_amber).strong().size(12.0));
                                ui.label(RichText::new(&current_card.gag_quote).color(Color32::from_rgb(255, 230, 200)).italics().size(12.0));
                            });
                    }

                    ui.add_space(10.0);
                    ui.separator();
                    ui.add_space(6.0);

                    // DUAL THAI SURVIVAL BRICK
                    ui.label(RichText::new("🇹🇭 SURVIVAL THAI BRICK (A0):").color(Color32::from_rgb(255, 110, 180)).strong().size(13.0));
                    ui.horizontal(|ui| {
                        ui.label(RichText::new(&current_card.thai_script).color(Color32::WHITE).size(22.0).strong());
                        ui.add_space(8.0);
                        ui.vertical(|ui| {
                            ui.label(RichText::new(&current_card.thai_phonetic).color(gold).strong().size(14.0));
                            ui.label(RichText::new(format!("Tones: {}", current_card.thai_tones)).color(Color32::LIGHT_BLUE).size(11.0));
                        });
                    });
                    if !current_card.thai_breakdown.is_empty() {
                        ui.label(RichText::new(&current_card.thai_breakdown).color(Color32::GRAY).size(11.0));
                    }
                });

                ui.add_space(10.0);

                // AUDIO ACTION TOOLBAR
                ui.horizontal(|ui| {
                    if ui.button(RichText::new("🇬🇧 English Audio (E)").color(Color32::WHITE)).clicked() {
                        self.play_audio_english();
                    }
                    if ui.button(RichText::new("🇹🇭 Thai Audio (T/R)").color(Color32::WHITE)).clicked() {
                        self.play_audio_thai();
                    }
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        let master_btn_text = if current_card.is_mastered {
                            "↩️ Move to Active"
                        } else {
                            "⭐ Mastered (M)"
                        };
                        if ui.button(RichText::new(master_btn_text).color(gold).strong()).clicked() {
                            self.toggle_master();
                        }
                    });
                });

                ui.add_space(6.0);

                // NAVIGATION BAR
                ui.horizontal(|ui| {
                    if ui.button(RichText::new("◄ Prev (A)").size(14.0)).clicked() {
                        if total_visible > 0 {
                            self.current_index = (self.current_index + total_visible - 1) % total_visible;
                        }
                    }

                    let flip_label = if current_card.is_revealed {
                        "🔄 Show Challenge (Space)"
                    } else {
                        "🔄 Show Solution (Space)"
                    };
                    if ui.button(RichText::new(flip_label).size(14.0).color(cyan)).clicked() {
                        if let Some(card_id) = self.visible_card_mut_id() {
                            if let Some(c) = self.cards.iter_mut().find(|c| c.id == card_id) {
                                c.is_revealed = !c.is_revealed;
                            }
                        }
                    }

                    if ui.button(RichText::new("Next (D) ►").size(14.0)).clicked() {
                        if total_visible > 0 {
                            self.current_index = (self.current_index + 1) % total_visible;
                        }
                    }
                });

                // Status Message Footer
                if let Some((msg, created_at)) = &self.status_message {
                    if created_at.elapsed() < Duration::from_secs(4) {
                        ui.add_space(8.0);
                        ui.label(RichText::new(msg).color(gold).size(12.0).italics());
                    }
                }
            });
    }
}

fn get_db_path() -> PathBuf {
    if let Ok(p) = std::env::var("LINGUO_DB_PATH") {
        PathBuf::from(p)
    } else {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        PathBuf::from(home).join(".local/share/linguo/history.db")
    }
}

fn load_cards_from_db(db_path: &Path) -> Result<Vec<LinguoCard>, rusqlite::Error> {
    let conn = Connection::open(db_path)?;
    let mut stmt = conn.prepare(
        "SELECT id, created_at, error_category, sprite_name, card_title, cefr_level, \
         card_type, front_challenge, back_solution, british_council_rule, gag_quote, \
         thai_script, thai_phonetic, thai_tones, thai_breakdown, \
         COALESCE(source_history_ids, ''), is_mastered \
         FROM cards ORDER BY is_mastered ASC, id ASC"
    )?;

    let card_iter = stmt.query_map([], |row| {
        Ok(LinguoCard {
            id: row.get(0)?,
            created_at: row.get(1)?,
            error_category: row.get(2)?,
            sprite_name: row.get(3)?,
            card_title: row.get(4)?,
            cefr_level: row.get(5)?,
            card_type: row.get(6)?,
            front_challenge: row.get(7)?,
            back_solution: row.get(8)?,
            british_council_rule: row.get(9)?,
            gag_quote: row.get(10)?,
            thai_script: row.get(11)?,
            thai_phonetic: row.get(12)?,
            thai_tones: row.get(13)?,
            thai_breakdown: row.get(14)?,
            source_history_ids: row.get(15)?,
            is_mastered: row.get::<_, i64>(16)? != 0,
            is_revealed: false,
        })
    })?;

    let mut result = Vec::new();
    for card in card_iter {
        result.push(card?);
    }
    Ok(result)
}

fn set_card_mastered_in_db(db_path: &Path, card_id: i64, mastered: bool) -> Result<(), rusqlite::Error> {
    let conn = Connection::open(db_path)?;
    conn.execute(
        "UPDATE cards SET is_mastered = ?1 WHERE id = ?2",
        params![if mastered { 1 } else { 0 }, card_id],
    )?;
    Ok(())
}

fn main() -> Result<(), eframe::Error> {
    let native_options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size(Vec2::new(540.0, 720.0))
            .with_min_inner_size(Vec2::new(480.0, 620.0))
            .with_title("Linguo // Active Recall Deck (16-bit MTG HUD)"),
        ..Default::default()
    };

    eframe::run_native(
        "Linguo // Active Recall Deck",
        native_options,
        Box::new(|cc| Ok(Box::new(LinguoGuiApp::new(cc)))),
    )
}
