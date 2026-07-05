use std::path::PathBuf;

use zed_extension_api::{self as zed, ContextServerId, LanguageServerId, Project, Result};

struct BackgroundRealtimeStt;

impl BackgroundRealtimeStt {
    fn extension_files_dir() -> Result<PathBuf> {
        let work_dir = std::env::current_dir().map_err(|error| format!("current_dir error: {error}"))?;

        let ext_id = work_dir
            .file_name()
            .ok_or("cannot get extension id from work dir")?
            .to_string_lossy()
            .into_owned();

        let extensions_dir = work_dir
            .parent()
            .and_then(|path| path.parent())
            .ok_or("cannot navigate to extensions dir")?;

        Ok(extensions_dir.join("installed").join(ext_id))
    }
}

impl zed::Extension for BackgroundRealtimeStt {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        let ext_files_dir = Self::extension_files_dir()?;
        let launcher = ext_files_dir.join("launcher.sh");
        let bash = worktree.which("bash").ok_or("bash not found in PATH")?;

        println!("[background-realtime-stt] launching LSP via {}", launcher.display());

        Ok(zed::Command {
            command: bash,
            args: vec![launcher.to_string_lossy().into_owned()],
            env: vec![],
        })
    }

    fn context_server_command(
        &mut self,
        _context_server_id: &ContextServerId,
        _project: &Project,
    ) -> Result<zed::Command> {
        let ext_files_dir = Self::extension_files_dir()?;
        let launcher = ext_files_dir.join("mcp-launcher.sh");

        println!(
            "[background-realtime-stt] launching context server via {}",
            launcher.display()
        );

        Ok(zed::Command {
            command: "/bin/bash".into(),
            args: vec![launcher.to_string_lossy().into_owned()],
            env: vec![],
        })
    }
}

zed::register_extension!(BackgroundRealtimeStt);
