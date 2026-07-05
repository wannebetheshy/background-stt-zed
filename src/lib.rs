use zed_extension_api::{self as zed, LanguageServerId, Result};

struct BackgroundRealtimeStt;

impl zed::Extension for BackgroundRealtimeStt {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        // current_dir = .../extensions/work/background-realtime-stt (пустой, WASM sandbox)
        // симлинк с файлами лежит на .../extensions/background-realtime-stt → наш проект
        let work_dir = std::env::current_dir()
            .map_err(|e| format!("current_dir error: {e}"))?;

        // поднимаемся из work/background-realtime-stt в extensions/
        let ext_id = work_dir
            .file_name()
            .ok_or("cannot get extension id from work dir")?
            .to_string_lossy()
            .into_owned();

        let extensions_dir = work_dir
            .parent() // .../extensions/work
            .and_then(|p| p.parent()) // .../extensions
            .ok_or("cannot navigate to extensions dir")?;

        // .../extensions/installed/background-realtime-stt — там реальные файлы
        let ext_files_dir = extensions_dir.join("installed").join(&ext_id);
        let launcher = ext_files_dir.join("launcher.sh");

        let bash = worktree.which("bash").ok_or("bash not found in PATH")?;

        println!("[background-realtime-stt] launching via {}", launcher.display());

        Ok(zed::Command {
            command: bash,
            args: vec![launcher.to_string_lossy().into_owned()],
            env: vec![],
        })
    }
}

zed::register_extension!(BackgroundRealtimeStt);
