package com.example.flap_bird_proj_extensao;

import java.awt.image.BufferedImage;
import java.io.File;
import java.io.PrintWriter;
import java.lang.reflect.Field;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.CountDownLatch;
import javafx.application.Platform;
import javafx.scene.SnapshotParameters;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.image.PixelReader;
import javafx.scene.image.WritableImage;
import javafx.scene.input.KeyCode;
import javafx.scene.input.KeyEvent;
import javafx.scene.paint.Color;
import javax.imageio.ImageIO;

/**
 * Ferramenta de documentação (fora do projeto): roda as classes REAIS do jogo (MenuState, PlayState, Bird, Pipe)
 * a partir do FlappyDrone.jar, sem janela, e salva quadros e medições. Nada aqui altera o jogo.
 */
public class Shots {
    static File out;
    static File data;
    static Canvas canvas = new Canvas(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT);
    static GraphicsContext gc = canvas.getGraphicsContext2D();
    static final double DT = 1.0 / 60.0;

    public static void main(String[] args) throws Exception {
        out = new File(args[0]);
        data = new File(args[1]);
        out.mkdirs();
        data.mkdirs();
        CountDownLatch started = new CountDownLatch(1);
        Platform.startup(started::countDown);
        started.await();
        CountDownLatch done = new CountDownLatch(1);
        Platform.runLater(() -> {
            try {
                run();
            } catch (Throwable t) {
                t.printStackTrace();
            } finally {
                done.countDown();
            }
        });
        done.await();
        Platform.exit();
        System.exit(0);
    }

    static void run() throws Exception {
        AssetManager.loadAssets();
        GameStateManager sm = new GameStateManager();

        MenuState menu = new MenuState(sm);
        menu.onEnter();
        for (int i = 0; i < 100; i++) menu.update(DT);
        menu.render(gc);
        save("01_menu.png");

        PlayState play = new PlayState(sm);
        play.onEnter();
        for (int i = 0; i < 60; i++) play.update(DT);
        play.render(gc);
        save("02_prepare-se.png");

        press(play);
        Bird bird = (Bird) get(play, "bird");
        boolean shotPlay = false;
        int frames = 0;
        while (frames++ < 60 * 90) {
            int score = (int) get(play, "score");
            if (score < 4) {
                autopilot(play, bird);
            } else if (!shotPlay) {
                play.render(gc);
                save("03_jogando.png");
                play.render(gc);
                overlayCollision(play, bird);
                save("04_colisao-circulo-e-retangulo.png");
                shotPlay = true;
            }
            play.update(DT);
            String phase = String.valueOf(get(play, "phase"));
            if (phase.equals("GAME_OVER") && (double) get(play, "gameOverTimer") > 1.2) break;
        }
        play.render(gc);
        save("05_fim-de-jogo.png");
        System.out.println("pontos na captura final: " + get(play, "score"));

        measurePhysics();
    }

    // ------------------------------------------------------------------ piloto de teste (só para gerar as imagens)
    static void press(PlayState play) {
        play.handleInput(new KeyEvent(KeyEvent.KEY_PRESSED, " ", " ", KeyCode.SPACE, false, false, false, false));
    }

    @SuppressWarnings("unchecked")
    static void autopilot(PlayState play, Bird bird) throws Exception {
        List<Pipe> pipes = (List<Pipe>) get(play, "pipes");
        double target = GameConfig.SCREEN_HEIGHT / 2.0;
        for (Pipe p : pipes) {
            BoundingBox bottom = (BoundingBox) get(p, "bottomBounds");
            if (bottom.x + GameConfig.PIPE_WIDTH > bird.getHitCenterX() - GameConfig.BIRD_HITBOX_RADIUS) {
                target = bottom.y - GameConfig.PIPE_GAP / 2.0 + 28;
                break;
            }
        }
        double vy = (double) get(bird, "velocityY");
        if (bird.getHitCenterY() > target && vy >= -50) press(play);
    }

    // ------------------------------------------------------------------ sobreposição didática (desenhada pela ferramenta)
    @SuppressWarnings("unchecked")
    static void overlayCollision(PlayState play, Bird bird) throws Exception {
        List<Pipe> pipes = (List<Pipe>) get(play, "pipes");
        gc.setLineWidth(2);
        for (Pipe p : pipes) {
            for (String name : new String[]{"topBounds", "bottomBounds"}) {
                BoundingBox b = (BoundingBox) get(p, name);
                gc.setFill(Color.web("#FF3B30", 0.18));
                gc.fillRect(b.x, b.y, b.width, b.height);
                gc.setStroke(Color.web("#FF3B30"));
                gc.strokeRect(b.x, b.y, b.width, b.height);
            }
        }
        double r = bird.getHitRadius();
        gc.setStroke(Color.web("#00FF7F"));
        gc.setLineWidth(3);
        gc.strokeOval(bird.getHitCenterX() - r, bird.getHitCenterY() - r, r * 2, r * 2);
    }

    // ------------------------------------------------------------------ medições da física (classe Bird de verdade)
    static void measurePhysics() throws Exception {
        try (PrintWriter w = new PrintWriter(new File(data, "trajetoria.csv"), "UTF-8")) {
            w.println("t;y_real_bird_dt60;y_antigo_dt60");
            Bird real = new Bird(400);
            real.jump();
            double yOld = 400, vOld = -600;
            for (int i = 0; i <= 100; i++) {
                w.printf(Locale.ROOT, "%.4f;%.3f;%.3f%n", i * DT, 400 - real.getY(), 400 - yOld);
                real.update(DT);
                vOld = Math.min(vOld + 1800 * DT, 800);
                yOld += vOld * DT;
            }
        }
        try (PrintWriter w = new PrintWriter(new File(data, "fisica.txt"), "UTF-8")) {
            for (double dt : new double[]{1.0 / 30, 1.0 / 60, 1.0 / 144, 1.0 / 240}) {
                Bird b = new Bird(400);
                b.jump();
                double minY = 400, tApex = 0, tBack = -1;
                int n = (int) Math.round(2.0 / dt);
                for (int i = 1; i <= n; i++) {
                    b.update(dt);
                    if (b.getY() < minY) {
                        minY = b.getY();
                        tApex = i * dt;
                    }
                    if (tBack < 0 && i * dt > 0.1 && b.getY() >= 400) tBack = i * dt;
                }
                w.printf(Locale.ROOT, "dt=1/%d apogeu=%.2f px em %.3f s; volta à altura inicial em %.3f s%n",
                        Math.round(1 / dt), 400 - minY, tApex, tBack);
            }
            // queda livre: velocidade ao longo do tempo (limite de queda)
            Bird b = new Bird(0);
            double prev = b.getY();
            double reach = -1;
            for (int i = 1; i <= 120; i++) {
                b.update(DT);
                double v = (b.getY() - prev) / DT;
                prev = b.getY();
                if (reach < 0 && v >= GameConfig.MAX_FALL_SPEED - 1e-6) reach = i * DT;
            }
            w.printf(Locale.ROOT, "queda livre: atinge MAX_FALL_SPEED=%.0f px/s em %.3f s%n", GameConfig.MAX_FALL_SPEED, reach);
        }
    }

    // ------------------------------------------------------------------ utilidades
    static Object get(Object o, String field) throws Exception {
        Class<?> c = o.getClass();
        while (c != null) {
            try {
                Field f = c.getDeclaredField(field);
                f.setAccessible(true);
                return f.get(o);
            } catch (NoSuchFieldException e) {
                c = c.getSuperclass();
            }
        }
        throw new NoSuchFieldException(field);
    }

    static void save(String name) throws Exception {
        SnapshotParameters params = new SnapshotParameters();
        params.setFill(Color.BLACK);
        WritableImage img = canvas.snapshot(params, null);
        PixelReader pr = img.getPixelReader();
        int w = (int) img.getWidth(), h = (int) img.getHeight();
        BufferedImage bi = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) bi.setRGB(x, y, pr.getArgb(x, y));
        ImageIO.write(bi, "png", new File(out, name));
        System.out.println("salvo " + new File(out, name));
    }
}
